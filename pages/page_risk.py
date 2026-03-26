import flet as ft
import numpy as np
import pandas as pd
from pymongo import MongoClient
from sklearn.ensemble import IsolationForest
from sklearn.metrics import mean_absolute_percentage_error
from datetime import datetime

TEXT = "#E2E8F0"
SUBTEXT = "#94A3B8"
CARD = "#1E293B"
BG = "#0F172A"
BORDER = "#334155"
ACCENT = "#38BDF8"

client = MongoClient("mongodb://localhost:27017/")
clean_db = client["inventory_ai_clean_db"]
db = client["inventory_full_system"]

collection = clean_db["cleaned_inventory"]
anomaly_collection = db["anomalies"]


def load_clean_data():
    rows = list(collection.find({}, {"_id": 0}))
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if "sale_date" in df.columns:
        df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")

    cols = [
        "quantity", "revenue", "discount", "current_stock", "stock_level",
        "rolling_demand", "stock_risk", "profit", "profit_margin",
        "cost_price", "selling_price", "turnover_ratio", "lead_time_days"
    ]

    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    return df


class RiskEngine:
    @staticmethod
    def safe(v):
        if v is None or pd.isna(v) or np.isinf(v):
            return 0
        return float(v)

    @staticmethod
    def stockout_risk(stock, demand):
        r = demand / max(stock, 1)
        s = min(int(r * 100), 100)
        return ("High 🔴", s) if s > 80 else ("Medium 🟡", s) if s > 50 else ("Low 🟢", s)

    @staticmethod
    def overstock_risk(stock, demand):
        r = stock / max(demand, 1)
        s = min(int(r * 20), 100)
        return ("High 🔴", s) if s > 80 else ("Medium 🟡", s) if s > 50 else ("Low 🟢", s)

    @staticmethod
    def profit_risk(margin):
        return ("High 🔴", 90) if margin < 0.2 else ("Medium 🟡", 60) if margin < 0.4 else ("Low 🟢", 30)

    @staticmethod
    def supplier_risk(lead):
        s = min(int(lead * 4), 100)
        return ("High 🔴", s) if s > 70 else ("Medium 🟡", s) if s > 40 else ("Low 🟢", s)

    @staticmethod
    def discount_risk(disc):
        s = min(int(disc * 3), 100)
        return ("High 🔴", s) if s > 70 else ("Medium 🟡", s) if s > 40 else ("Low 🟢", s)

    @staticmethod
    def anomaly_detection(hist):
        if len(hist) < 10:
            return []
        model = IsolationForest(contamination=0.08)
        pred = model.fit_predict(np.array(hist).reshape(-1, 1))
        return [i for i, p in enumerate(pred) if p == -1]

    @staticmethod
    def forecast_accuracy(vals):
        if len(vals) < 5:
            return None
        arr = np.array(vals)
        pred = np.roll(arr, 1)
        pred[0] = arr.mean()
        mape = mean_absolute_percentage_error(arr, pred)
        return round((1 - mape) * 100, 2)


def save_anomaly(pid, qty, row):
    anomaly_collection.insert_one({
        "product_id": pid,
        "quantity": float(qty),
        "invoice_number": row.get("invoice_number"),
        "sale_date": row.get("sale_date"),
        "detected_at": datetime.utcnow(),
        "message": "Demand anomaly detected"
    })


class RiskCard(ft.Container):
    def __init__(self, title, level, score, icon):
        super().__init__(
            width=260,
            padding=20,
            border_radius=20,
            bgcolor=CARD,
            border=ft.border.all(1, BORDER),
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=ACCENT),
                    ft.Text(title, weight="bold", color=TEXT)
                ]),
                ft.Text(level, color=SUBTEXT),
                ft.ProgressBar(value=score / 100, color=ACCENT),
                ft.Text(f"{score}%", color=SUBTEXT)
            ])
        )


def build_risk_page(page: ft.Page):
    df = load_clean_data()

    if df.empty:
        return ft.Text("No data found", color=TEXT)

    dropdown = ft.Dropdown(
        label="Select Product",
        width=250,
        bgcolor="white",
        color=TEXT,
        border_color=BORDER,
        focused_border_color=ACCENT,
        options=[ft.dropdown.Option(p) for p in sorted(df["product_id"].unique())],
    )

    grid = ft.ResponsiveRow()

    insights = ft.Container(
        padding=20,
        bgcolor=CARD,
        border_radius=16,
        border=ft.border.all(1, BORDER),
        content=ft.Text("AI Insights will appear here...", color=TEXT)
    )

    def analyze(e):
        grid.controls.clear()
        pid = dropdown.value
        if not pid:
            return

        pdf = df[df["product_id"] == pid]
        latest = pdf.iloc[-1]

        stock = latest.get("stock_level", 0)
        demand = latest.get("rolling_demand", 0)
        discount = latest.get("discount", 0)
        lead = latest.get("lead_time_days", 0)
        margin = latest.get("profit_margin", 0)

        hist = pdf["quantity"].tolist()

        r1 = RiskEngine.stockout_risk(stock, demand)
        r2 = RiskEngine.overstock_risk(stock, demand)
        r3 = RiskEngine.profit_risk(margin)
        r4 = RiskEngine.supplier_risk(lead)
        r5 = RiskEngine.discount_risk(discount)

        anomalies = RiskEngine.anomaly_detection(hist)
        acc = RiskEngine.forecast_accuracy(hist)

        cards = [
            RiskCard("Stockout", *r1, ft.Icons.WARNING),
            RiskCard("Overstock", *r2, ft.Icons.INVENTORY),
            RiskCard("Profit", *r3, ft.Icons.PAID),
            RiskCard("Supplier", *r4, ft.Icons.LOCAL_SHIPPING),
            RiskCard("Discount", *r5, ft.Icons.PERCENT),
        ]

        grid.controls.extend([
            ft.Container(c, col={"sm": 6, "md": 4, "xl": 3}) for c in cards
        ])

        summary = f"""AI SUMMARY:

• Forecast Accuracy: {acc if acc else "N/A"}%
• Demand Trend: {"High" if demand > stock else "Stable"}
• Risk: {r1[0]}, {r2[0]}
• Action: {"Increase stock" if demand > stock else "Reduce stock"}
"""
        insights.content = ft.Text(summary, color=TEXT)

        avg = np.mean(hist) if hist else 0

        for idx in anomalies:
            row = pdf.iloc[idx]
            qty = row.get("quantity", 0)
            date = row.get("sale_date", "Unknown")
            inv = row.get("invoice_number", "N/A")

            if qty > avg:
                reason = "Demand spike detected"
                action = "Increase stock to meet demand"
            else:
                reason = "Demand drop detected"
                action = "Review sales and reduce inventory"

            save_anomaly(pid, qty, row)

            grid.controls.append(
                ft.Container(
                    bgcolor="#7F1D1D",
                    padding=12,
                    border_radius=10,
                    content=ft.Column([
                        ft.Text("🚨 Anomaly Detected", weight="bold", color="white"),
                        ft.Text(f"Qty: {qty}", color="white"),
                        ft.Text(f"Date: {date}", color="white"),
                        ft.Text(f"Invoice: {inv}", color="white"),
                        ft.Text(f"Reason: {reason}", color="white"),
                        ft.Text(f"Suggestion: {action}", color="white"),
                    ])
                )
            )

        page.update()

    return ft.Container(
        expand=True,
        bgcolor=BG,
        padding=20,
        content=ft.Column([
            ft.Row([
                ft.Text("🚀 AI Risk Intelligence", size=28, weight="bold", color=TEXT),
                ft.Container(expand=True),
                dropdown,
                ft.FilledButton(
                    "Analyze",
                    on_click=analyze,
                    style=ft.ButtonStyle(bgcolor=ACCENT, color="black")
                )
            ]),
            ft.Divider(color=BORDER),
            grid,
            ft.Divider(color=BORDER),
            ft.Text("🧠 AI Insights", size=20, weight="bold", color=TEXT),
            insights,
        ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    )