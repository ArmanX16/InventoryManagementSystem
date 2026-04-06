import flet as ft
from pymongo import MongoClient
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
from io import BytesIO

from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
from prophet import Prophet

# ---------------- DataBase ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client["inventoryai"]
collection = db["cleaned_inventory"]


# ---------------- Image Encodings----------------
def fig_to_base64(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode()
    buffer.close()
    plt.close(fig)
    return encoded


# ---------------- Data load ----------------
def load_product_data(pid):
    rows = list(collection.find({"product_id": pid}, {"_id": 0}))
    df = pd.DataFrame(rows)

    if df.empty:
        return df

    #-------------------------Date----------------------
    if "date" in df.columns:
        df["sale_date"] = pd.to_datetime(df["date"], errors="coerce")
    elif "order_date" in df.columns:
        df["sale_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    else:
        df["sale_date"] = pd.to_datetime(df.get("created_at"), errors="coerce")

    df = df.sort_values("sale_date")


    df["quantity"] = pd.to_numeric(df.get("quantity", 0), errors="coerce").fillna(0)
    df["discount"] = pd.to_numeric(df.get("discount", 0), errors="coerce").fillna(0)
    df["current_stock"] = pd.to_numeric(df.get("current_stock", 0), errors="coerce").fillna(0)
    df["profit"] = pd.to_numeric(df.get("profit", 0), errors="coerce").fillna(0)
    df["turnover_ratio"] = pd.to_numeric(df.get("turnover_ratio", 0), errors="coerce").fillna(0)
    df["risk_score"] = pd.to_numeric(df.get("risk_score", 0), errors="coerce").fillna(0)


    df["lag_1"] = df["quantity"].shift(1)
    df["lag_7"] = df["quantity"].shift(7)
    df["rolling_7"] = df["quantity"].rolling(7).mean()
    df["rolling_30"] = df["quantity"].rolling(30).mean()

    df.fillna(0, inplace=True)

    return df


# ---------------- Random forest model ----------------
def rf_model(df, days):
    features = [
        "lag_1", "lag_7", "rolling_7", "rolling_30",
        "discount", "current_stock", "profit",
        "turnover_ratio", "risk_score"
    ]

    X, y = df[features], df["quantity"]
    split = max(int(len(df) * 0.8), 1)

    model = RandomForestRegressor(n_estimators=400, random_state=42)
    model.fit(X[:split], y[:split])

    preds = model.predict(X[split:])
    mape = mean_absolute_percentage_error(y[split:], preds) if len(preds) > 0 else 0
    rmse = np.sqrt(mean_squared_error(y[split:], preds)) if len(preds) > 0 else 0

    row = X.iloc[-1:].copy()
    output = []

    for _ in range(days):
        p = model.predict(row)[0]
        output.append(p)
        row["lag_1"] = p
        row["rolling_7"] = np.mean(output[-7:])

    return output, mape, rmse


# ---------------- xgboost----------------
def xgb_model(df, days):
    features = [
        "lag_1", "lag_7", "rolling_7", "rolling_30",
        "discount", "current_stock",
        "profit", "turnover_ratio", "risk_score"
    ]

    X, y = df[features], df["quantity"]
    split = max(int(len(df) * 0.8), 1)

    model = xgb.XGBRegressor(n_estimators=300, learning_rate=0.05)
    model.fit(X[:split], y[:split])

    preds = model.predict(X[split:])
    mape = mean_absolute_percentage_error(y[split:], preds) if len(preds) > 0 else 0
    rmse = np.sqrt(mean_squared_error(y[split:], preds)) if len(preds) > 0 else 0

    row = X.iloc[-1:].copy()
    output = []

    for _ in range(days):
        p = model.predict(row)[0]
        output.append(p)
        row["lag_1"] = p
        row["rolling_7"] = np.mean(output[-7:])

    return output, mape, rmse


# ---------------- Prophet----------------
def prophet_model(df, days):
    p_df = df[["sale_date", "quantity"]].dropna()
    p_df.columns = ["ds", "y"]

    model = Prophet()
    model.fit(p_df)

    future = model.make_future_dataframe(periods=days)
    forecast = model.predict(future)

    yhat = forecast["yhat"].values[-days:]
    lower = forecast["yhat_lower"].values[-days:]
    upper = forecast["yhat_upper"].values[-days:]

    rmse = np.sqrt(mean_squared_error(p_df["y"], forecast["yhat"][:len(p_df)]))
    mape = mean_absolute_percentage_error(p_df["y"], forecast["yhat"][:len(p_df)])

    return yhat, lower, upper, mape, rmse


# ---------------- UI----------------------
def stat_card(t, v):
    return ft.Container(
        width=230,
        height=90,
        bgcolor="#1e293b",
        border_radius=14,
        padding=15,
        content=ft.Column([
            ft.Text(t, size=14, color="white70"),
            ft.Text(v, size=24, weight="bold", color="white")
        ])
    )


# ---------------- Main ----------------
def build_forecast_page(page: ft.Page):
    chart_box = ft.Container()

    product_list = collection.distinct("product_id")

    dd_product = ft.Dropdown(
        label="Product",
        width=260,
        options=[ft.dropdown.Option(p) for p in product_list],
        color="white"
    )

    dd_model = ft.Dropdown(
        label="Model",
        value="RandomForest",
        width=200,
        options=[
            ft.dropdown.Option("RandomForest"),
            ft.dropdown.Option("XGBoost"),
            ft.dropdown.Option("Prophet")
        ],
        color="white"
    )

    dd_days = ft.Dropdown(
        label="Days",
        value="30",
        width=150,
        options=[
            ft.dropdown.Option("7"),
            ft.dropdown.Option("30"),
            ft.dropdown.Option("90")
        ],
        color="white"
    )

    c1 = stat_card("Expected Demand", "-")
    c2 = stat_card("Recommended Stock", "-")
    c3 = stat_card("Model Confidence", "-")
    c4 = stat_card("Expected Revenue", "-")

    insight = ft.Text(size=16, color="white")

    def run(e):
        pid = dd_product.value
        model = dd_model.value
        days = int(dd_days.value)

        df = load_product_data(pid)

        if df.empty:
            insight.value = "No data found for this product"
            page.update()
            return

        if model == "RandomForest":
            fc, mape, rmse = rf_model(df, days)
            low = np.array(fc) * 0.9
            high = np.array(fc) * 1.1

        elif model == "XGBoost":
            fc, mape, rmse = xgb_model(df, days)
            low = np.array(fc) * 0.9
            high = np.array(fc) * 1.1

        else:
            fc, low, high, mape, rmse = prophet_model(df, days)

        total = int(sum(fc))

        price = df["selling_price"].iloc[-1] if "selling_price" in df else 1000
        revenue = int(total * price)

        # UPDATE UI
        c1.content.controls[1].value = str(total)
        c2.content.controls[1].value = str(int(total * 1.2))
        c3.content.controls[1].value = f"{max(0, (1 - mape) * 100):.1f}%"
        c4.content.controls[1].value = str(revenue)

        trend = "increasing" if fc[-1] > fc[0] else "stable or decreasing"

        insight.value = (
            f"Forecast: {total} units in next {days} days. "
            f"Trend: {trend}. "
            f"Recommended stock: {int(total * 1.2)} units. "
            f"Revenue estimate: ₹{revenue}."
        )

        fig, ax = plt.subplots()
        ax.plot(fc)
        ax.set_title("Demand Forecast")

        img = fig_to_base64(fig)

        chart_box.content = ft.Image(
            src="data:image/png;base64," + img,
            fit="contain"
        )

        page.update()

    return ft.Container(
        expand=True,
        bgcolor="#0f172a",
        padding=20,
        content=ft.Column(
            [
                ft.Text("AI Demand Forecast", size=32, weight="bold", color="white"),

                ft.Row(
                    [dd_product, dd_model, dd_days, ft.ElevatedButton("Run Forecast", on_click=run)],
                    wrap=True
                ),

                ft.Row([c1, c2, c3, c4], wrap=True),

                insight,

                ft.Container(content=chart_box, height=400)
            ],
            spacing=20,
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )
    )