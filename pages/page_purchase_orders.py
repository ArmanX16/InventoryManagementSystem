import flet as ft
from datetime import datetime, timedelta
from data.database import db

products_col = db["products"]
suppliers_col = db["suppliers"]
purchase_col = db["purchase_orders"]
counters_col = db["counters"]

from ui.theme import (
    ACCENT_PRIMARY, COLOR_DANGER, COLOR_WARNING,
    COLOR_SUCCESS, TEXT_PRIMARY, TEXT_SECONDARY,
    SURFACE_DARK, BORDER_DEFAULT,
)
from ui.components import build_page_header, build_card


def get_next_po():
    counter = counters_col.find_one_and_update(
        {"_id": "po_counter"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return f"PO{counter['seq']}"


def build_purchase_orders_page(flet_page: ft.Page):

    selected_id = {"value": None}

    # ── LOAD DROPDOWNS ────────────────────────────────────
    def load_products():
        return [
            ft.dropdown.Option(
                key=p["product_id"],
                text=f"{p['product_id']} - {p['name']}"
            )
            for p in products_col.find({}, {"product_id": 1, "name": 1}).limit(100)
        ]

    def load_suppliers():
        return [
            ft.dropdown.Option(
                key=str(s["_id"]),
                text=f"{s['_id']} - {s['name']}"
            )
            for s in suppliers_col.find({}, {"_id": 1, "name": 1}).limit(100)
        ]

    # ── FIELDS ────────────────────────────────────────────
    field_style = {
        "color": TEXT_PRIMARY,
        "bgcolor": SURFACE_DARK,
        "border_color": BORDER_DEFAULT,
        "focused_border_color": ACCENT_PRIMARY,
        "width": 220,
    }

    product_dd = ft.Dropdown(
        label="Product", width=280,
        options=load_products(),
        color=TEXT_PRIMARY, bgcolor=SURFACE_DARK,
        border_color=BORDER_DEFAULT,
    )
    supplier_dd = ft.Dropdown(
        label="Supplier", width=280,
        options=load_suppliers(),
        color=TEXT_PRIMARY, bgcolor=SURFACE_DARK,
        border_color=BORDER_DEFAULT,
    )
    quantity_f     = ft.TextField(label="Quantity", **field_style, keyboard_type=ft.KeyboardType.NUMBER)
    order_date_f   = ft.TextField(label="Order Date (YYYY-MM-DD)", value=str(datetime.now().date()), **field_style)
    delivery_f     = ft.TextField(label="Expected Delivery", **field_style)
    delay_dd = ft.Dropdown(
        label="Delay", width=220,
        options=[ft.dropdown.Option("False"), ft.dropdown.Option("True")],
        value="False",
        color=TEXT_PRIMARY, bgcolor=SURFACE_DARK,
        border_color=BORDER_DEFAULT,
    )
    error_text = ft.Text("", color="red", size=12)
    table_column = ft.Column([])

    # ── AUTO DELIVERY ─────────────────────────────────────
    def calc_delivery(e=None):
        sup = suppliers_col.find_one({"_id": supplier_dd.value})
        if not sup:
            return
        lead_days = int(sup.get("avg_lead_time", 7))
        try:
            od = datetime.strptime(order_date_f.value, "%Y-%m-%d")
        except:
            od = datetime.now()
        delivery_f.value = str((od + timedelta(days=lead_days)).date())
        flet_page.update()

    supplier_dd.on_change = calc_delivery

    # ── BUILD ROWS ────────────────────────────────────────
    def build_rows(po_list):
        rows = []
        for po in po_list:
            prod = products_col.find_one({"product_id": po["product_id"]})
            sup = suppliers_col.find_one({"_id": po["supplier_id"]})
            status = po.get("status", "Pending")
            status_color = (
                COLOR_SUCCESS if status == "Delivered"
                else COLOR_DANGER if status in ["Rejected", "Not Available"]
                else COLOR_WARNING
            )

            def on_tap(e, data=po):
                fill_fields(data)

            rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(po["_id"]), color=TEXT_PRIMARY, size=12), on_tap=on_tap),
                    ft.DataCell(ft.Text(prod["name"] if prod else po["product_id"], color=TEXT_PRIMARY, size=12)),
                    ft.DataCell(ft.Text(sup["name"] if sup else po["supplier_id"], color=TEXT_SECONDARY, size=12)),
                    ft.DataCell(ft.Text(str(po["quantity"]), color=TEXT_PRIMARY, size=12)),
                    ft.DataCell(ft.Text(str(po.get("order_date", ""))[:10], color=TEXT_SECONDARY, size=12)),
                    ft.DataCell(ft.Text(status, color=status_color, size=12, weight=ft.FontWeight.W_600)),
                ]
            ))
        return rows

    # ── REFRESH TABLE ─────────────────────────────────────
    def refresh_table():
        pos = list(purchase_col.find().limit(100))
        from ui.components import build_data_table
        table_column.controls.clear()
        table_column.controls.append(
            build_data_table(
                column_labels=["PO ID", "Product", "Supplier", "Qty", "Order Date", "Status"],
                table_rows=build_rows(pos),
            )
        )
        flet_page.update()

    # ── FILL FIELDS ───────────────────────────────────────
    def fill_fields(po):
        selected_id["value"] = po["_id"]
        product_dd.value = po["product_id"]
        supplier_dd.value = po["supplier_id"]
        quantity_f.value = str(po["quantity"])
        order_date_f.value = str(po.get("order_date", ""))[:10]
        delivery_f.value = str(po.get("expected_delivery", ""))[:10]
        delay_dd.value = str(po.get("delay_flag", False))
        flet_page.update()

    # ── CLEAR ─────────────────────────────────────────────
    def clear_fields(e=None):
        selected_id["value"] = None
        product_dd.value = None
        supplier_dd.value = None
        quantity_f.value = ""
        order_date_f.value = str(datetime.now().date())
        delivery_f.value = ""
        delay_dd.value = "False"
        error_text.value = ""
        flet_page.update()

    # ── ADD ───────────────────────────────────────────────
    def add_po(e):
        if not product_dd.value or not supplier_dd.value or not quantity_f.value:
            error_text.value = "⚠ Product, Supplier and Quantity required."
            flet_page.update()
            return
        if not delivery_f.value:
            error_text.value = "⚠ Please enter Expected Delivery date."
            flet_page.update()
            return
        try:
            po_id = get_next_po()
            purchase_col.insert_one({
                "_id": po_id,
                "product_id": product_dd.value,
                "supplier_id": supplier_dd.value,
                "quantity": int(quantity_f.value),
                "order_date": datetime.strptime(order_date_f.value, "%Y-%m-%d"),
                "expected_delivery": datetime.strptime(delivery_f.value, "%Y-%m-%d"),
                "status": "Pending",
                "delay_flag": delay_dd.value == "True"
            })
            error_text.value = ""
            clear_fields()
            refresh_table()
        except Exception as ex:
            error_text.value = f"⚠ Error: {ex}"
            flet_page.update()

    # ── UPDATE ────────────────────────────────────────────
    def update_po(e):
        if not selected_id["value"]:
            error_text.value = "⚠ Select a PO first."
            flet_page.update()
            return
        purchase_col.update_one(
            {"_id": selected_id["value"]},
            {"$set": {
                "product_id": product_dd.value,
                "supplier_id": supplier_dd.value,
                "quantity": int(quantity_f.value),
                "order_date": datetime.strptime(order_date_f.value, "%Y-%m-%d"),
                "expected_delivery": datetime.strptime(delivery_f.value, "%Y-%m-%d"),
                "delay_flag": delay_dd.value == "True"
            }}
        )
        clear_fields()
        refresh_table()

    # ── DELETE ────────────────────────────────────────────
    def delete_po(e):
        if not selected_id["value"]:
            error_text.value = "⚠ Select a PO first."
            flet_page.update()
            return
        purchase_col.delete_one({"_id": selected_id["value"]})
        clear_fields()
        refresh_table()

    # ── INITIAL LOAD ──────────────────────────────────────
    refresh_table()

    # ── FORM CARD ─────────────────────────────────────────
    form_card = build_card(
        ft.Column([
            ft.Text("Purchase Order Form", size=15, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
            ft.Container(height=8),
            ft.Row([product_dd, supplier_dd], spacing=12),
            ft.Row([quantity_f, order_date_f], spacing=12),
            ft.Row([delivery_f, delay_dd], spacing=12),
            ft.Container(height=8),
            error_text,
            ft.Row([
                ft.ElevatedButton("Add", bgcolor=COLOR_SUCCESS, color="white", on_click=add_po),
                ft.ElevatedButton("Update", bgcolor=ACCENT_PRIMARY, color="white", on_click=update_po),
                ft.ElevatedButton("Delete", bgcolor=COLOR_DANGER, color="white", on_click=delete_po),
                ft.ElevatedButton("Clear", on_click=clear_fields),
            ], spacing=12),
        ], spacing=10)
    )

    # ── RETURN PAGE ───────────────────────────────────────
    return ft.Column(
        [
            build_page_header(
                header_title="Purchase Orders",
                header_subtitle="Manage purchase orders",
                header_icon=ft.Icons.SHOPPING_CART,
            ),
            ft.Container(height=20),
            form_card,
            ft.Container(height=16),
            build_card(
                ft.Column([
                    ft.Text("All Purchase Orders", size=15, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                    ft.Container(height=12),
                    table_column,
                ])
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )