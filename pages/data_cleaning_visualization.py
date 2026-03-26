import flet as ft
from pymongo import MongoClient
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import IsolationForest
import base64
from io import BytesIO

client = MongoClient("mongodb://localhost:27017/")

raw_db = client["inventory_full_system"]
clean_db = client["inventory_ai_clean_db"]

def fig_to_b64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return img

def load_col(name):
    data = list(raw_db[name].find({}, {"_id": 0}))
    return pd.DataFrame(data)

def txt_clean(df):
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].astype(str).str.strip()
        df[c] = df[c].replace(["", "nan", "None", "null"], np.nan)
    return df

def to_num(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def fill_num(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].fillna(df[c].median())
    return df

def clip_outliers(df, col):
    if col not in df.columns:
        return df
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    up = q3 + 1.5 * iqr
    df[col] = df[col].clip(low, up)
    return df

def mongo_safe(df):
    df = df.replace({np.nan: None})
    df = df.replace({pd.NaT: None})
    return df

def clean_products(df):
    if df.empty:
        return df

    df = txt_clean(df)
    df = df.drop_duplicates(subset=["sku"])

    nums = [
        "cost_price","selling_price","current_stock","safety_stock",
        "lead_time_days","reorder_point","turnover_ratio","risk_score"
    ]

    df = to_num(df, nums)
    df = fill_num(df, nums)

    for c in nums:
        df = clip_outliers(df, c)

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")

    df["price"] = df["selling_price"]
    df["stock_level"] = df["current_stock"]

    return df

def clean_suppliers(df):
    if df.empty:
        return df

    df = txt_clean(df)

    nums = ["avg_lead_time","reliability_score","delay_days_avg","cost_rating"]
    df = to_num(df, nums)
    df = fill_num(df, nums)

    return df

def clean_sales(df):
    if df.empty:
        return df

    df = txt_clean(df)

    nums = ["quantity","revenue","discount"]
    df = to_num(df, nums)
    df = fill_num(df, nums)

    for c in nums:
        df = clip_outliers(df, c)

    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    return df

def clean_employees(df):
    if df.empty:
        return df

    df = txt_clean(df)

    nums = ["salary","performance_score","total_sales"]
    df = to_num(df, nums)
    df = fill_num(df, nums)

    df["dob"] = pd.to_datetime(df["dob"], errors="coerce")
    return df

def clean_customers(df):
    if df.empty:
        return df

    df = txt_clean(df)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df

def clean_invoices(df):
    if df.empty:
        return df

    nums = ["total_amount","discount","net_amount"]
    df = to_num(df, nums)
    df = fill_num(df, nums)

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df

def clean_purchase_orders(df):
    if df.empty:
        return df

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["expected_delivery"] = pd.to_datetime(df["expected_delivery"], errors="coerce")

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["quantity"] = df["quantity"].fillna(df["quantity"].median())

    return df

def clean_anomalies(df):
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["anomaly_score"] = pd.to_numeric(df["anomaly_score"], errors="coerce")
    df["anomaly_score"] = df["anomaly_score"].fillna(df["anomaly_score"].median())

    return df

def feature_engineering(sales, products):
    df = sales.merge(products, on="product_id", how="left")

    df["profit"] = df["revenue"] - (df["quantity"] * df["cost_price"])
    df["profit_margin"] = df["profit"] / df["revenue"].replace(0, np.nan)

    df["month"] = df["sale_date"].dt.month
    df["weekday"] = df["sale_date"].dt.weekday
    df["weekend"] = df["weekday"].isin([5, 6]).astype(int)

    df["stock_risk"] = (df["stock_level"] < df["safety_stock"]).astype(int)

    df["rolling_demand"] = df.groupby("product_id")["quantity"].transform(
        lambda x: x.rolling(7, 1).mean()
    )

    return df

def detect_anomalies(df):
    model = IsolationForest(contamination=0.05)

    X = df[["quantity","revenue","profit"]].fillna(0)
    df["anomaly"] = model.fit_predict(X)
    df["anomaly"] = df["anomaly"].map({1: 0, -1: 1})

    return df

def generate_insights(df):
    out = []

    out.append(f"Total Revenue: {round(df['revenue'].sum(),2)}")
    out.append(f"Total Profit: {round(df['profit'].sum(),2)}")
    out.append(f"Units Sold: {int(df['quantity'].sum())}")
    out.append(f"Avg Profit Margin: {round(df['profit_margin'].mean()*100,2)}%")

    risky = df[df["stock_risk"] == 1].shape[0]
    out.append(f"Products With Stock Risk: {risky}")

    anomalies = df[df["anomaly"] == 1].shape[0]
    out.append(f"Detected Sales Anomalies: {anomalies}")

    return "\n".join(out)

def demand_chart(df):
    d = df.groupby("sale_date")["quantity"].sum()
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(d)
    ax.set_title("Demand Trend")
    return fig_to_b64(fig)

def correlation_chart(df):
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(df.select_dtypes(include=np.number).corr(), cmap="coolwarm", ax=ax)
    ax.set_title("Feature Correlation")
    return fig_to_b64(fig)

def profit_chart(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(df["profit"], bins=40, ax=ax)
    ax.set_title("Profit Distribution")
    return fig_to_b64(fig)

def anomaly_chart(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(x=df["quantity"], y=df["revenue"], hue=df["anomaly"], ax=ax)
    ax.set_title("Anomaly Detection")
    return fig_to_b64(fig)

def run_pipeline():
    products = clean_products(load_col("products"))
    sales = clean_sales(load_col("sales"))
    employees = clean_employees(load_col("employees"))
    suppliers = clean_suppliers(load_col("suppliers"))
    customers = clean_customers(load_col("customers"))
    invoices = clean_invoices(load_col("invoices"))
    purchase_orders = clean_purchase_orders(load_col("purchase_orders"))
    anomalies = clean_anomalies(load_col("anomalies"))

    df = feature_engineering(sales, products)
    df = detect_anomalies(df)
    df = mongo_safe(df)

    clean_db.cleaned_inventory.delete_many({})
    recs = df.to_dict("records")

    if recs:
        clean_db.cleaned_inventory.insert_many(recs)

    return df

def build_data_cleaning_visualization_page(page: ft.Page):

    page.title = "Enterprise Inventory AI Cleaner"

    status = ft.Text(color="#1F2937")
    insights = ft.Text(color="#1F2937")
    chart = ft.Container(expand=True)

    def run(e):
        df = run_pipeline()
        insights.value = generate_insights(df)
        status.value = "Cleaning completed successfully"
        page.update()

    def show(func):
        df = pd.DataFrame(list(clean_db.cleaned_inventory.find({}, {"_id": 0})))

        if df.empty:
            status.value = "No cleaned data available. Run pipeline first."
            page.update()
            return

        img = func(df)

        chart.content = ft.Image(
            src="data:image/png;base64," + img,
            expand=True,
            fit="contain"
        )

        page.update()

    return ft.Container(
        expand=True,
        bgcolor="#F5F7FA",
        padding=20,
        content=ft.Column(
            [
                ft.Text(
                    "Enterprise Inventory AI Cleaning System",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color="#111827"
                ),

                ft.Row(
                    [
                        ft.FilledButton("Run AI Cleaning", on_click=run),
                        ft.OutlinedButton("Demand Trend", on_click=lambda e: show(demand_chart)),
                        ft.OutlinedButton("Correlation", on_click=lambda e: show(correlation_chart)),
                        ft.OutlinedButton("Profit Distribution", on_click=lambda e: show(profit_chart)),
                        ft.OutlinedButton("Anomaly Detection", on_click=lambda e: show(anomaly_chart)),
                    ],
                    wrap=True
                ),

                status,

                ft.Text("Business Insights", size=20, color="#111827"),
                insights,

                ft.Container(
                    content=chart,
                    expand=True,
                    bgcolor="white",
                    border_radius=12,
                    padding=12,
                    border=ft.border.all(1, "#E5E7EB"),
                    shadow=ft.BoxShadow(
                        blur_radius=10,
                        color=ft.Colors.with_opacity(0.1, "black"),
                        offset=ft.Offset(0, 4)
                    )
                ),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=15
        )
    )