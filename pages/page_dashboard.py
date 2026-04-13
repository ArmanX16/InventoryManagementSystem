import flet as ft
from pymongo import MongoClient
import pandas as pd
import numpy as np

from ui.theme import (
    ACCENT_PRIMARY,
    ACCENT_SECONDARY,
    COLOR_DANGER,
    COLOR_WARNING,
    COLOR_SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

from ui.components import (
    build_card,
    build_status_badge,
    build_section_title,
    build_stat_card,
    build_data_table,
    build_mini_bar_chart,
)

client = MongoClient("mongodb://localhost:27017/")
db = client["inventoryai"]
collection = db["cleaned_inventory"]

# 🔥 CACHE (IMPORTANT)
_cached_df = None


# ---------------- FAST LOAD ----------------
def load_data():
    global _cached_df

    if _cached_df is not None:
        return _cached_df

    # 🔥 LIMIT DATA (MOST IMPORTANT FIX)
    data = list(collection.find({}, {"_id": 0}).limit(3000))

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # 🔥 FAST DATE HANDLING
    if "date" in df.columns:
        df["sale_date"] = pd.to_datetime(df["date"], errors="coerce")
    elif "created_at" in df.columns:
        df["sale_date"] = pd.to_datetime(df["created_at"], errors="coerce")
    else:
        df["sale_date"] = pd.Timestamp("today")

    # 🔥 FAST NUMERIC CONVERSION
    numeric_cols = ["qty", "quantity", "total", "selling_price", "cost_price", "current_stock"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["quantity"] = df["qty"] if "qty" in df.columns else df.get("quantity", 0)
    df["stock_level"] = df.get("current_stock", 0)

    # 🔥 VECTOR CALCULATION (FASTER)
    df["revenue"] = df.get("total", df["selling_price"] * df["quantity"])
    df["profit"] = (df.get("selling_price", 0) - df.get("cost_price", 0)) * df["quantity"]

    _cached_df = df
    return df


# ---------------- MAIN ----------------
def build_dashboard_page(flet_page: ft.Page):
    df = load_data()

    if df.empty:
        return ft.Text("No data available", color="white")

    # 🔥 FAST GROUPING
    latest = df.sort_values("sale_date").groupby("product_id", as_index=False).last()

    total_products = latest["product_id"].nunique()

    reorder = latest.get("reorder_point", pd.Series([0]*len(latest)))

    low_stock = len(latest[latest["stock_level"] <= reorder])
    out_stock = len(latest[latest["stock_level"] == 0])
    total_revenue = int(df["revenue"].sum())

    # ---------------- ALERTS ----------------
    alerts = []
    for _, r in latest.head(200).iterrows():  # 🔥 LIMIT LOOP
        if r["stock_level"] == 0:
            alerts.append({
                "type": "danger",
                "title": f"{r.get('name','Item')} Out of Stock",
                "msg": "Immediate restock required",
                "time": "now"
            })
        elif r["stock_level"] <= r.get("reorder_point", 0):
            alerts.append({
                "type": "warning",
                "title": f"{r.get('name','Item')} Low Stock",
                "msg": "Reorder soon",
                "time": "now"
            })

    alerts = alerts[:5]

    alert_widgets = ft.Column([
        ft.Row([
            ft.Container(
                width=8,
                height=8,
                border_radius=4,
                bgcolor=(COLOR_DANGER if a["type"] == "danger" else COLOR_WARNING),
            ),
            ft.Column([
                ft.Text(a["title"], size=13, color=TEXT_PRIMARY),
                ft.Text(a["msg"], size=11, color=TEXT_SECONDARY),
            ], spacing=1, expand=True),
            ft.Text(a["time"], size=11, color=TEXT_SECONDARY),
        ])
        for a in alerts
    ])

    # 🔥 FAST TOP PRODUCTS
    top_df = df.groupby("product_id")["quantity"].sum().nlargest(5)
    top_products = latest.set_index("product_id").loc[top_df.index].reset_index()

    rows = [
        ft.DataRow(cells=[
            ft.DataCell(ft.Text(r.get("name", ""), color=TEXT_PRIMARY)),
            ft.DataCell(ft.Text(str(r.get("category_id", "")), color=TEXT_SECONDARY)),
            ft.DataCell(ft.Text(
                str(r["stock_level"]),
                color=COLOR_SUCCESS if r["stock_level"] > r.get("reorder_point", 0) else COLOR_DANGER
            )),
            ft.DataCell(ft.Text(f"₹{r.get('selling_price',0)}", color=TEXT_PRIMARY)),
        ])
        for _, r in top_products.iterrows()
    ]

    # 🔥 FAST CHART
    cat_data = df.groupby("category_id")["revenue"].sum().nlargest(4)

    chart = build_mini_bar_chart(
        bar_values=cat_data.values.tolist(),
        bar_labels=cat_data.index.tolist(),
        bar_color=ACCENT_PRIMARY,
    )

    inventory_chart_card = build_card(
        ft.Column([
            ft.Text("Inventory by Category", size=15, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
            ft.Container(height=10),
            chart
        ]),
        should_expand=True
    )

    live_alerts_card = build_card(
        ft.Column([
            ft.Row([
                ft.Text("Live Alerts", size=15, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                build_status_badge(str(len(alerts)), COLOR_DANGER)
            ]),
            ft.Container(height=10),
            alert_widgets
        ]),
        should_expand=True
    )

    top_products_card = build_card(
        ft.Column([
            ft.Text("Top Products Overview", size=15, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
            ft.Container(height=10),
            build_data_table(
                column_labels=["Product", "Category", "Stock", "Price"],
                table_rows=rows
            )
        ])
    )

    trend = "increasing" if df["quantity"].tail(10).mean() > df["quantity"].head(10).mean() else "stable"

    insight_text = (
        f"Sales trend is {trend}. "
        f"Total revenue ₹{total_revenue}. "
        f"Monitor low stock items to avoid loss."
    )

    insight_card = build_card(
        ft.Column([
            ft.Text("AI Insight", size=15, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
            ft.Container(height=10),
            ft.Text(insight_text, color=TEXT_SECONDARY)
        ])
    )

    return ft.Column(
        [
            build_section_title("AI Smart Dashboard", "Real-time inventory intelligence"),
            ft.Container(height=20),

            ft.ResponsiveRow([
                ft.Column([build_stat_card(ft.Icons.INVENTORY, "Total Products", total_products, 5, ACCENT_PRIMARY)], col={"xs": 12, "sm": 6, "md": 3}),
                ft.Column([build_stat_card(ft.Icons.WARNING, "Low Stock Items", low_stock, -10, COLOR_WARNING)], col={"xs": 12, "sm": 6, "md": 3}),
                ft.Column([build_stat_card(ft.Icons.MONEY_OFF, "Out of Stock", out_stock, -100, COLOR_DANGER)], col={"xs": 12, "sm": 6, "md": 3}),
                ft.Column([build_stat_card(ft.Icons.RECEIPT, "Revenue", total_revenue, 8, ACCENT_SECONDARY)], col={"xs": 12, "sm": 6, "md": 3}),
            ]),

            ft.Container(height=20),

            ft.ResponsiveRow([
                ft.Column([inventory_chart_card], col={"xs": 12, "md": 7}),
                ft.Column([live_alerts_card], col={"xs": 12, "md": 5}),
            ]),

            ft.Container(height=20),

            insight_card,

            ft.Container(height=20),

            top_products_card,
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )