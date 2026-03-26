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

client = MongoClient("mongodb://localhost:27017/")
db = client["inventory_ai_clean_db"]
collection = db["cleaned_inventory"]


def fig_to_base64(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode()
    buffer.close()
    plt.close(fig)
    return encoded


def load_product_data(pid):
    rows = list(collection.find({"product_id": pid}, {"_id": 0}))
    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df = df.sort_values("sale_date")

    df["lag_1"] = df["quantity"].shift(1)
    df["lag_7"] = df["quantity"].shift(7)
    df["rolling_7"] = df["quantity"].rolling(7).mean()
    df["rolling_30"] = df["quantity"].rolling(30).mean()

    df.fillna(0, inplace=True)

    return df


def rf_model(df, days):
    f = ["lag_1","lag_7","rolling_7","rolling_30","discount","stock_level","profit_margin",
         "month","weekday","weekend","turnover_ratio","risk_score","stock_risk"]

    X, y = df[f], df["quantity"]
    split = int(len(df) * 0.8)

    m = RandomForestRegressor(n_estimators=400, random_state=42)
    m.fit(X[:split], y[:split])

    preds = m.predict(X[split:])
    mape = mean_absolute_percentage_error(y[split:], preds)
    rmse = np.sqrt(mean_squared_error(y[split:], preds))

    row = X.iloc[-1:].copy()
    out = []

    for _ in range(days):
        p = m.predict(row)[0]
        out.append(p)
        row["lag_1"] = p

    return out, mape, rmse


def xgb_model(df, days):
    f = ["lag_1","lag_7","rolling_7","rolling_30","discount","stock_level","profit_margin",
         "month","weekday","weekend","turnover_ratio","risk_score"]

    X, y = df[f], df["quantity"]
    split = int(len(df) * 0.8)

    m = xgb.XGBRegressor(n_estimators=300, learning_rate=0.05)
    m.fit(X[:split], y[:split])

    preds = m.predict(X[split:])
    mape = mean_absolute_percentage_error(y[split:], preds)
    rmse = np.sqrt(mean_squared_error(y[split:], preds))

    row = X.iloc[-1:].copy()
    out = []

    for _ in range(days):
        p = m.predict(row)[0]
        out.append(p)
        row["lag_1"] = p

    return out, mape, rmse


def prophet_model(df, days):
    p_df = df[["sale_date", "quantity"]]
    p_df.columns = ["ds", "y"]

    m = Prophet()
    m.fit(p_df)

    future = m.make_future_dataframe(periods=days)
    forecast = m.predict(future)

    yhat = forecast["yhat"].values[-days:]
    lower = forecast["yhat_lower"].values[-days:]
    upper = forecast["yhat_upper"].values[-days:]

    rmse = np.sqrt(mean_squared_error(p_df["y"], forecast["yhat"][:len(p_df)]))
    mape = mean_absolute_percentage_error(p_df["y"], forecast["yhat"][:len(p_df)])

    return yhat, lower, upper, mape, rmse


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
        price = df["selling_price"].iloc[-1]
        revenue = int(total * price)

        c1.content.controls[1].value = str(total)
        c2.content.controls[1].value = str(int(total * 1.25))
        c3.content.controls[1].value = f"{(1-mape)*100:.1f}%"
        c4.content.controls[1].value = str(revenue)

        trend = "increasing" if fc[-1] > fc[0] else "stable or decreasing"

        insight.value = (
            f"Forecast indicates {total} units may be sold in next {days} days. "
            f"Demand trend appears {trend}. "
            f"Recommended to keep stock around {int(total*1.25)} units. "
            f"Estimated revenue could reach ₹{revenue}."
        )

        fig, ax = plt.subplots()
        ax.plot(fc)
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
                ft.Text("AI Demand Forecast Intelligence", size=32, weight="bold", color="white"),

                ft.Row([dd_product, dd_model, dd_days, ft.ElevatedButton("Run Forecast", on_click=run)], wrap=True),

                ft.Row([c1, c2, c3, c4], wrap=True),

                insight,

                ft.Container(content=chart_box, height=400)
            ],
            spacing=20,
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )
    )