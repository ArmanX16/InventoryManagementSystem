import flet as ft
from pymongo import MongoClient
from datetime import datetime
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import statistics

# ================= DATABASE =================
client = MongoClient("mongodb://localhost:27017/")
db = client["inventory"]
ai_db = client["inventoryai"]

products_col = db["products"]
sales_col = db["sales"]
employees_col = db["employees"]
customers_col = db["customers"]
suppliers_col = db["suppliers"]

# 🔥 UPDATED (use cleaned_inventory)
ai_sales_col = ai_db["cleaned_inventory"]

# ================= UTILS =================
def chart_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    return img

# ================= AI ANALYTICS =================
def get_ai_metrics():
    data = list(ai_sales_col.find())

    if not data:
        return {"profit": 0, "anomaly_count": 0, "avg_profit": 0, "clusters": {}}

    profits = [d.get("profit", 0) for d in data]
    anomalies = [d.get("anomaly", 0) for d in data]

    cluster_count = {}
    for d in data:
        c = d.get("cluster", "Unknown")
        cluster_count[c] = cluster_count.get(c, 0) + 1

    return {
        "profit": sum(profits),
        "anomaly_count": sum(anomalies),
        "avg_profit": statistics.mean(profits),
        "clusters": cluster_count
    }

# ================= CHARTS =================
def sales_trend_chart():
    data = list(sales_col.find())
    dates = {}

    for d in data:
        date = d.get("date", "Unknown")
        dates[date] = dates.get(date, 0) + d.get("total", 0)

    fig, ax = plt.subplots()
    ax.plot(list(dates.keys()), list(dates.values()))
    ax.set_title("Sales Trend")

    return chart_to_base64(fig)

def profit_trend_chart():
    data = list(ai_sales_col.find())
    months = {}

    for d in data:
        m = d.get("month", "Unknown")
        months[m] = months.get(m, 0) + d.get("profit", 0)

    fig, ax = plt.subplots()
    ax.plot(list(months.keys()), list(months.values()))
    ax.set_title("Profit Trend")

    return chart_to_base64(fig)

def stock_chart():
    data = list(products_col.find())

    names = [p["name"] for p in data][:10]
    stock = [p.get("current_stock", 0) for p in data][:10]

    fig, ax = plt.subplots()
    ax.plot(names, stock)
    ax.set_title("Stock Levels")

    return chart_to_base64(fig)

# ================= CRUD =================
def add_employee(name, email):
    employees_col.insert_one({
        "name": name,
        "email": email,
        "created_at": str(datetime.now())
    })

def delete_employee(emp_id):
    employees_col.delete_one({"employee_id": emp_id})

def update_employee(emp_id, name):
    employees_col.update_one(
        {"employee_id": emp_id},
        {"$set": {"name": name}}
    )

# ================= GENERIC DB VIEWER =================
def build_collection_table(collection):
    data = list(collection.find().limit(20))

    if not data:
        return ft.Text("No data")

    columns = list(data[0].keys())

    table_rows = []
    for d in data:
        row = ft.Row([
            ft.Text(str(d.get(col, ""))[:20], size=10)
            for col in columns[:6]  # limit columns for UI
        ])
        table_rows.append(row)

    return ft.Column(table_rows, scroll=ft.ScrollMode.AUTO, height=200)

# ================= UI HELPERS =================
def build_card(content):
    return ft.Container(
        content=content,
        bgcolor="white",
        padding=15,
        border_radius=12,
        expand=True
    )

# ================= MAIN PAGE =================
def build_admin_page(page: ft.Page):

    page.scroll = None
    page.bgcolor = "#f5f6fa"

    ai_metrics = get_ai_metrics()

    # ===== STATS =====
    stats_row = ft.ResponsiveRow([
        ft.Container(ft.Text(f"Profit\n{ai_metrics['profit']}"), col={"md": 3}),
        ft.Container(ft.Text(f"Anomalies\n{ai_metrics['anomaly_count']}"), col={"md": 3}),
        ft.Container(ft.Text(f"Avg Profit\n{round(ai_metrics['avg_profit'],2)}"), col={"md": 3}),
        ft.Container(ft.Text(f"Clusters\n{len(ai_metrics['clusters'])}"), col={"md": 3}),
    ])

    # ===== CHARTS =====
    charts_section = ft.ResponsiveRow([
        ft.Container(ft.Image(src="data:image/png;base64," + sales_trend_chart()), col={"md": 4}),
        ft.Container(ft.Image(src="data:image/png;base64," + profit_trend_chart()), col={"md": 4}),
        ft.Container(ft.Image(src="data:image/png;base64," + stock_chart()), col={"md": 4}),
    ])

    # ===== EMPLOYEE =====
    name_field = ft.TextField(label="Name", dense=True)
    email_field = ft.TextField(label="Email", dense=True)

    employee_list = ft.Column(scroll=ft.ScrollMode.AUTO, height=200)

    def load_employees():
        employee_list.controls.clear()
        for e in employees_col.find():
            employee_list.controls.append(
                ft.Row([
                    ft.Text(e.get("name"), expand=True),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        on_click=lambda ev, id=e.get("employee_id"): delete_emp(id)
                    )
                ])
            )
        page.update()

    def add_emp(e):
        add_employee(name_field.value, email_field.value)
        load_employees()

    def delete_emp(emp_id):
        delete_employee(emp_id)
        load_employees()

    load_employees()

    employee_card = build_card(
        ft.Column([
            ft.Text("Employee Management", size=16),
            name_field,
            email_field,
            ft.ElevatedButton("Add", on_click=add_emp),
            employee_list
        ])
    )

    # ===== ALERTS =====
    alerts = ft.Column(scroll=ft.ScrollMode.AUTO, height=200)

    def load_alerts():
        alerts.controls.clear()
        for p in products_col.find():
            if p.get("current_stock", 0) < p.get("safety_stock", 0):
                alerts.controls.append(ft.Text(f"⚠ {p['name']} Low Stock"))
        page.update()

    load_alerts()

    alerts_card = build_card(
        ft.Column([
            ft.Text("Stock Alerts", size=16),
            alerts
        ])
    )

    # ===== 🔥 DATABASE VIEWER =====
    db_view = ft.ResponsiveRow([
        ft.Column([
            build_card(ft.Column([
                ft.Text("Products"),
                build_collection_table(products_col)
            ]))
        ], col={"md": 6}),

        ft.Column([
            build_card(ft.Column([
                ft.Text("AI Cleaned Data"),
                build_collection_table(ai_sales_col)
            ]))
        ], col={"md": 6}),
    ])

    # ===== FINAL =====
    return ft.Container(
        content=ft.Column([
            ft.Text("Admin Dashboard", size=22, weight=ft.FontWeight.BOLD),
            stats_row,
            build_card(charts_section),
            ft.ResponsiveRow([
                ft.Column([employee_card], col={"md": 6}),
                ft.Column([alerts_card], col={"md": 6}),
            ]),
            db_view  # 🔥 added without breaking UI
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True),
        expand=True
    )