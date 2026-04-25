import flet as ft
from datetime import datetime, timedelta
from data.database import db
import threading
import time

from sklearn.linear_model import LinearRegression
import numpy as np

products_col = db["products"]
purchase_col = db["purchase_orders"]
suppliers_col = db["suppliers"]
counters_col = db["counters"]
auto_po_col = db["auto_purchase_history"]

from ui.theme import *
from ui.components import build_page_header, build_card


def get_next_po():
    counter = counters_col.find_one_and_update(
        {"_id": "po_counter"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return f"PO{counter['seq']}"


def train_ai_model():
    data = list(products_col.find())

    X, y = [], []
    for d in data:
        try:
            stock = int(d.get("current_stock", 0))
            reorder = int(d.get("reorder_point", 0))
            lead = int(d.get("lead_time_days", 1))
            turnover = int(d.get("turnover_ratio", 1))

            X.append([stock, reorder, lead, turnover])
            y.append(max(reorder * 2, 10))
        except:
            continue

    if not X:
        return None

    model = LinearRegression()
    model.fit(np.array(X), np.array(y))
    return model


def build_reorder_page(flet_page: ft.Page):

    ai_mode = {"value": False}
    ai_model = {"model": None}

    low_stock_column = ft.Column([])
    auto_table_column = ft.Column([])
    notification = ft.Text("", color=COLOR_WARNING)

    def safe_update():
        try:
            flet_page.update()
        except:
            pass

    # ─────────────────────────────
    # LOW STOCK DISPLAY
    # ─────────────────────────────
    def refresh_low_stock():
        low_stock_column.controls.clear()

        for p in products_col.find():
            try:
                stock = int(p.get("current_stock", 0))
                reorder = int(p.get("reorder_point", 0))

                if stock < reorder:
                    low_stock_column.controls.append(
                        ft.Text(
                            f"{p['name']} → Stock: {stock}",
                            color="red",
                            weight=ft.FontWeight.BOLD
                        )
                    )
            except:
                continue

    # ─────────────────────────────
    # AUTO TABLE
    # ─────────────────────────────
    def refresh_auto_table():
        rows = []

        for po in auto_po_col.find().sort("created_at", -1).limit(50):
            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(po.get("po_id", ""))),
                    ft.DataCell(ft.Text(po.get("product", ""))),
                    ft.DataCell(ft.Text(str(po.get("predicted_qty", "")))),
                    ft.DataCell(ft.Text(str(po.get("created_at", ""))[:19])),
                ])
            )

        auto_table_column.controls.clear()
        auto_table_column.controls.append(ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("PO ID")),
                ft.DataColumn(ft.Text("Product")),
                ft.DataColumn(ft.Text("Qty")),
                ft.DataColumn(ft.Text("Time")),
            ],
            rows=rows
        ))

    # ─────────────────────────────
    # AI ENGINE
    # ─────────────────────────────
    def auto_engine():
        while ai_mode["value"]:
            model = ai_model["model"]

            for p in products_col.find():
                try:
                    stock = int(p.get("current_stock", 0))
                    reorder = int(p.get("reorder_point", 0))
                    lead = int(p.get("lead_time_days", 1))
                    turnover = max(int(p.get("turnover_ratio", 1)), 1)

                    # SMART CONDITION
                    if stock < reorder and (stock / turnover) < lead:

                        # avoid duplicate PO
                        exists = purchase_col.find_one({
                            "product_id": p["product_id"],
                            "status": "Auto"
                        })

                        if exists:
                            continue

                        pred_qty = int(model.predict([[stock, reorder, lead, turnover]])[0])

                        po_id = get_next_po()

                        purchase_col.insert_one({
                            "_id": po_id,
                            "product_id": p["product_id"],
                            "supplier_id": p.get("supplier_id"),
                            "quantity": pred_qty,
                            "order_date": datetime.now(),
                            "expected_delivery": datetime.now() + timedelta(days=lead),
                            "status": "Auto"
                        })

                        auto_po_col.insert_one({
                            "po_id": po_id,
                            "product": p["name"],
                            "predicted_qty": pred_qty,
                            "created_at": datetime.now()
                        })

                        notification.value = f"⚠ Auto reordered: {p['name']}"

                except:
                    continue

            refresh_low_stock()
            refresh_auto_table()
            safe_update()
            time.sleep(8)

    def start_ai():
        threading.Thread(target=auto_engine, daemon=True).start()

    def toggle_ai(e):
        ai_mode["value"] = e.control.value
        if ai_mode["value"]:
            ai_model["model"] = train_ai_model()
            notification.value = "🤖 AI ACTIVE"
            start_ai()
        else:
            notification.value = "🛑 AI STOPPED"
        safe_update()

    ai_switch = ft.Switch(label="AI Auto Reorder", on_change=toggle_ai)

    refresh_low_stock()
    refresh_auto_table()

    return ft.Column(
        [
            build_page_header(
                header_title="Smart Reorder System",
                header_subtitle="Fully Automated AI Inventory",
                header_icon=ft.Icons.PSYCHOLOGY,
            ),

            ft.Row([ai_switch]),
            notification,

            build_card(ft.Column([
                ft.Text("⚠ Low Stock Items", color="white"),
                low_stock_column
            ])),

            build_card(ft.Column([
                ft.Text("🤖 Auto Reorder History", color="white"),
                auto_table_column
            ])),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )