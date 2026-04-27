import flet as ft
from pymongo import MongoClient
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans

import base64
from io import BytesIO
from datetime import datetime

import os
import uuid

client = MongoClient("mongodb://localhost:27017/")
raw_db = client["inventory"]
clean_db = client["inventoryai"]


def save_chart_and_get_b64(fig, chart_name):
    folder = "charts"
    os.makedirs(folder, exist_ok=True)

    unique_name = f"{chart_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.png"
    full_path = os.path.join(folder, unique_name)

    fig.savefig(
        full_path,
        format="png",
        bbox_inches="tight",
        dpi=180
    )

    buf = BytesIO()
    fig.savefig(
        buf,
        format="png",
        bbox_inches="tight",
        dpi=180
    )
    buf.seek(0)

    img = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)

    return img

def fig_to_b64(fig, chart_name="chart"):
    return save_chart_and_get_b64(fig, chart_name)


def load(name):
    data = list(raw_db[name].find())
    return pd.DataFrame(data) if data else pd.DataFrame()


def drop_mongo_ids(df):
    for col in ["_id", "_id_x", "_id_y"]:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)
    return df


def remove_unhashable(df):
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].astype(str)
    return df



def safe_merge(left, right, on=None, left_on=None, right_on=None, prefix="x"):
    if right.empty:
        return left

    right = right.copy()

    join_cols = set()
    if on:
        join_cols.update([on] if isinstance(on, str) else on)
    if left_on:
        join_cols.add(left_on)
    if right_on:
        join_cols.add(right_on)

    rename_map = {}
    for col in right.columns:
        if col in left.columns and col not in join_cols:
            rename_map[col] = f"{prefix}_{col}"

    right.rename(columns=rename_map, inplace=True)

    return pd.merge(
        left,
        right,
        on=on,
        left_on=left_on,
        right_on=right_on,
        how="left"
    )



def generate_insights(df):
    if df.empty:
        return ["No Data"]

    df["revenue"] = df["total"]
    df["quantity"] = df["qty"]
    df["profit_margin"] = np.where(df["revenue"] == 0, 0, df["profit"] / df["revenue"])

    return [
        f"Total Revenue: {round(df['revenue'].sum(),2)}",
        f"Total Profit: {round(df['profit'].sum(),2)}",
        f"Units Sold: {int(df['quantity'].sum())}",
        f"Avg Profit Margin: {round(df['profit_margin'].mean()*100,2)}%",
    ]



def safe_month(df):
    if "date" in df.columns:
        df["date"] = df["date"].astype(str).fillna("unknown")
        df["month"] = df["date"].str[:7]
    else:
        df["month"] = "unknown"
    return df



def demand_chart(df):
    df = df.dropna(subset=["month"])

    grouped = df.groupby("month").agg({
        "qty": "sum",
        "profit": "sum",
        "total": "sum"
    }).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(
        grouped["month"],
        grouped["qty"],
        marker="o",
        linewidth=3,
        label="Units Sold"
    )

    ax.plot(
        grouped["month"],
        grouped["profit"],
        marker="s",
        linewidth=3,
        label="Profit"
    )

    ax.plot(
        grouped["month"],
        grouped["total"],
        marker="^",
        linewidth=3,
        label="Revenue"
    )

    ax.set_title("Demand / Revenue / Profit Trend", fontsize=15, weight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Value")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.xticks(rotation=45)

    return fig_to_b64(fig, "demand_trend")


def profit_chart(df):
    fig, ax = plt.subplots()
    sns.histplot(df["profit"].fillna(0), bins=30, ax=ax)
    return fig_to_b64(fig)


def correlation_chart(df):
    fig, ax = plt.subplots(figsize=(14, 9))

    num_df = df.select_dtypes(include=np.number).fillna(0)

    corr = num_df.corr()

    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        cmap="coolwarm",
        ax=ax,
        annot_kws={
            "size": 9,
            "color": "black"
        }
    )

    ax.set_title("Business Correlation Heatmap", fontsize=15, weight="bold")

    return fig_to_b64(fig, "correlation_heatmap")


def anomaly_chart(df):
    fig, ax = plt.subplots()
    sns.scatterplot(x=df["qty"], y=df["profit"], hue=df["anomaly"], ax=ax)
    return fig_to_b64(fig)



def build_data_cleaning_visualization_page(page: ft.Page):

    page.bgcolor = "white"

    status = ft.Text("")
    chart = ft.Container()
    insights_box = ft.Column()

    def run(e):
        try:
            status.value = "Running..."
            page.update()


            products = remove_unhashable(load("products"))
            sales = remove_unhashable(load("sales"))
            customers = load("customers")
            suppliers = load("suppliers")
            categories = load("categories")
            employees = load("employees")
            invoices = remove_unhashable(load("invoices"))
            purchase_orders = load("purchase_orders")


            for df in [products, sales, customers, suppliers, categories, employees, invoices, purchase_orders]:
                if not df.empty:
                    df.drop_duplicates(inplace=True)
                    for col in df.columns:
                        df[col] = df[col].fillna("Unknown")


            if "date" in sales.columns:
                sales["date"] = sales["date"].astype(str).fillna("unknown")
            else:
                sales["date"] = "unknown"

            merged = sales.copy()

            # MERGE
            merged = safe_merge(merged, products, on="product_id", prefix="prod")
            merged = safe_merge(merged, customers, on="customer_id", prefix="cust")
            merged = safe_merge(merged, suppliers, on="supplier_id", prefix="sup")
            merged = safe_merge(merged, employees, on="employee_id", prefix="emp")
            merged = safe_merge(merged, categories, left_on="category_id", right_on="_id", prefix="cat")
            merged = safe_merge(merged, invoices, on="invoice_id", prefix="inv")
            merged = safe_merge(merged, purchase_orders, on="product_id", prefix="po")


            merged = safe_month(merged)


            for col in ["selling_price", "cost_price", "qty", "total"]:
                if col not in merged:
                    merged[col] = 0

            merged["selling_price"] = pd.to_numeric(merged["selling_price"], errors="coerce").fillna(0)
            merged["cost_price"] = pd.to_numeric(merged["cost_price"], errors="coerce").fillna(0)
            merged["qty"] = pd.to_numeric(merged["qty"], errors="coerce").fillna(0)
            merged["total"] = pd.to_numeric(merged["total"], errors="coerce").fillna(0)


            merged["profit"] = (merged["selling_price"] - merged["cost_price"]) * merged["qty"]

            data = merged[["qty", "total", "profit"]].fillna(0)


            iso = IsolationForest(contamination=0.05, random_state=42)
            merged["anomaly"] = iso.fit_predict(data) if len(data) > 10 else 1

            try:
                kmeans = KMeans(n_clusters=3, random_state=42)
                merged["cluster"] = kmeans.fit_predict(data)
            except:
                merged["cluster"] = 0

            merged["run_timestamp"] = str(datetime.now())


            clean_db.cleaned_inventory.delete_many({})


            merged = drop_mongo_ids(merged)


            merged = merged.replace({np.nan: None})

            clean_db.cleaned_inventory.insert_many(merged.to_dict("records"))

            insights_box.controls = [ft.Text(i) for i in generate_insights(merged)]

            status.value = "Done ✅"
            page.update()

        except Exception as ex:
            print("🔥 ERROR:", ex)
            status.value = str(ex)
            page.update()

    def show(func):
        df = pd.DataFrame(list(clean_db.cleaned_inventory.find({}, {"_id": 0})))

        if df.empty:
            status.value = "Run cleaning first"
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
        bgcolor="white",
        padding=20,
        content=ft.Column(
            [
                ft.Text("Enterprise Inventory AI System", size=28, weight="bold"),

                ft.Row(
                    [
                        ft.FilledButton("Run Full AI Pipeline", on_click=run),
                        ft.OutlinedButton("Demand", on_click=lambda e: show(demand_chart)),
                        ft.OutlinedButton("Profit", on_click=lambda e: show(profit_chart)),
                        ft.OutlinedButton("Correlation", on_click=lambda e: show(correlation_chart)),
                        ft.OutlinedButton("Anomaly", on_click=lambda e: show(anomaly_chart)),
                    ]
                ),

                status,
                chart,
                ft.Text("Insights", size=20, weight="bold"),
                insights_box
            ],
            scroll="auto"
        )
    )