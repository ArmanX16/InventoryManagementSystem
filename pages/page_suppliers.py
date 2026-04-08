import flet as ft
from datetime import datetime
from data.database import db
from ui.theme import (
    ACCENT_PRIMARY, ACCENT_SECONDARY,
    COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING,
    TEXT_PRIMARY, TEXT_SECONDARY,
    SURFACE_DARK, BORDER_DEFAULT,
)
from ui.components import (
    build_card, build_status_badge, build_page_header,
    build_stat_card, build_data_table, build_action_button,
)

suppliers_col = db["suppliers"]
products_col = db["products"]
po_col = db["purchase_orders"]


def build_suppliers_page(flet_page: ft.Page):

    # ── LOAD DATA ─────────────────────────────────────────
    def get_suppliers():
        return list(suppliers_col.find().limit(100))

    suppliers = get_suppliers()

    # ── STATS ─────────────────────────────────────────────
    total = len(suppliers)

    # ── TABLE COLUMN ──────────────────────────────────────
    table_column = ft.Column([])
    selected_po = {"value": None}

    # ── SUPPLIER TABLE ────────────────────────────────────
    def build_supplier_rows(sup_list):
        rows = []
        for s in sup_list:
            rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(s.get("_id", "")), color=TEXT_SECONDARY, size=12)),
                    ft.DataCell(ft.Text(s.get("name", ""), color=TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(str(s.get("contact", "")), color=TEXT_SECONDARY, size=12)),
                    ft.DataCell(ft.Text(str(s.get("email", "")), color=TEXT_SECONDARY, size=12)),
                    ft.DataCell(ft.Text(str(s.get("reliability_score", "")), color=COLOR_WARNING, size=12)),
                    ft.DataCell(ft.Text(str(s.get("avg_lead_time", "")), color=ACCENT_PRIMARY, size=12)),
                ]
            ))
        return rows

    def refresh_suppliers():
        sups = get_suppliers()
        from ui.components import build_data_table
        table_column.controls.clear()
        table_column.controls.append(
            build_data_table(
                column_labels=["ID", "Name", "Contact", "Email", "Reliability", "Lead Time"],
                table_rows=build_supplier_rows(sups),
            )
        )
        flet_page.update()

    # ── SUPPLIER APPROVAL SECTION ─────────────────────────
    po_id_f      = ft.TextField(label="PO ID", width=180, disabled=True, color=TEXT_PRIMARY, bgcolor=SURFACE_DARK, border_color=BORDER_DEFAULT)
    product_id_f = ft.TextField(label="Product ID", width=180, disabled=True, color=TEXT_PRIMARY, bgcolor=SURFACE_DARK, border_color=BORDER_DEFAULT)
    supplier_id_f = ft.TextField(label="Supplier ID", width=180, disabled=True, color=TEXT_PRIMARY, bgcolor=SURFACE_DARK, border_color=BORDER_DEFAULT)
    quantity_f   = ft.TextField(label="Delivered Qty", width=180, color=TEXT_PRIMARY, bgcolor=SURFACE_DARK, border_color=BORDER_DEFAULT, keyboard_type=ft.KeyboardType.NUMBER)

    status_dd = ft.Dropdown(
        label="Update Status", width=220,
        options=[
            ft.dropdown.Option("Delivered"),
            ft.dropdown.Option("Rejected"),
            ft.dropdown.Option("Not Available"),
        ],
        color=TEXT_PRIMARY, bgcolor=SURFACE_DARK,
        border_color=BORDER_DEFAULT,
    )

    po_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("PO ID", color=TEXT_PRIMARY)),
            ft.DataColumn(ft.Text("Product", color=TEXT_PRIMARY)),
            ft.DataColumn(ft.Text("Supplier", color=TEXT_PRIMARY)),
            ft.DataColumn(ft.Text("Qty", color=TEXT_PRIMARY)),
            ft.DataColumn(ft.Text("Status", color=TEXT_PRIMARY)),
        ],
        rows=[]
    )

    def load_po_table():
        po_table.rows.clear()
        for po in po_col.find().limit(100):
            def select_row(ev, data=po):
                selected_po["value"] = data
                po_id_f.value = str(data["_id"])
                product_id_f.value = data["product_id"]
                supplier_id_f.value = data["supplier_id"]
                quantity_f.value = str(data["quantity"])
                status_dd.value = None
                flet_page.update()

            status = po.get("status", "Pending")
            status_color = (
                COLOR_SUCCESS if status == "Delivered"
                else COLOR_DANGER if status in ["Rejected", "Not Available"]
                else COLOR_WARNING
            )
            po_table.rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(po["_id"]), color=TEXT_PRIMARY, size=12), on_tap=select_row),
                    ft.DataCell(ft.Text(po["product_id"], color=TEXT_SECONDARY, size=12)),
                    ft.DataCell(ft.Text(po["supplier_id"], color=TEXT_SECONDARY, size=12)),
                    ft.DataCell(ft.Text(str(po["quantity"]), color=TEXT_PRIMARY, size=12)),
                    ft.DataCell(ft.Text(status, color=status_color, size=12, weight=ft.FontWeight.W_600)),
                ]
            ))
        flet_page.update()

    def update_po(e):
        if not selected_po["value"]:
            return
        new_status = status_dd.value
        if not new_status:
            return
        po = selected_po["value"]
        try:
            new_qty = int(quantity_f.value)
        except:
            return
        if new_qty < 0:
            return

        po_col.update_one(
            {"_id": po["_id"]},
            {"$set": {
                "quantity": new_qty,
                "status": new_status,
                "delay_flag": False if new_status == "Delivered" else True
            }}
        )

        if new_status == "Delivered":
            product = products_col.find_one({"product_id": po["product_id"]})
            if product:
                try:
                    current = int(product.get("current_stock", 0))
                except:
                    current = 0
                products_col.update_one(
                    {"product_id": po["product_id"]},
                    {"$set": {
                        "current_stock": current + new_qty,
                        "updated_at": datetime.utcnow()
                    }}
                )

        selected_po["value"] = None
        po_id_f.value = ""
        product_id_f.value = ""
        supplier_id_f.value = ""
        quantity_f.value = ""
        status_dd.value = None
        load_po_table()

    # ── INITIAL LOAD ──────────────────────────────────────
    refresh_suppliers()
    load_po_table()

    # ── RETURN PAGE ───────────────────────────────────────
    return ft.Column(
        [
            build_page_header(
                header_title="Suppliers Management",
                header_subtitle="Manage your supplier network",
                header_icon=ft.Icons.LOCAL_SHIPPING,
            ),
            ft.Container(height=20),

            # Stats
            ft.ResponsiveRow([
                ft.Column([build_stat_card(ft.Icons.LOCAL_SHIPPING, "Total Suppliers", total, None, ACCENT_PRIMARY)], col={"xs": 6, "md": 3}),
                ft.Column([build_stat_card(ft.Icons.STAR, "Avg Reliability", "7.5", None, COLOR_WARNING)], col={"xs": 6, "md": 3}),
                ft.Column([build_stat_card(ft.Icons.ACCESS_TIME, "Avg Lead Time", "8 days", None, ACCENT_SECONDARY)], col={"xs": 6, "md": 3}),
                ft.Column([build_stat_card(ft.Icons.SHOPPING_CART, "Total POs", po_col.count_documents({}), None, COLOR_SUCCESS)], col={"xs": 6, "md": 3}),
            ], spacing=16),

            ft.Container(height=20),

            # Suppliers table
            build_card(ft.Column([
                ft.Text("All Suppliers", size=15, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ft.Container(height=12),
                table_column,
            ])),

            ft.Container(height=20),

            # Supplier approval section
            build_card(ft.Column([
                ft.Text("Supplier Order Approval", size=15, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ft.Container(height=12),
                ft.Row([po_id_f, product_id_f, supplier_id_f], spacing=12),
                ft.Row([quantity_f, status_dd], spacing=12),
                ft.Container(height=8),
                ft.ElevatedButton(
                    "Update Order",
                    bgcolor=ACCENT_PRIMARY,
                    color="white",
                    on_click=update_po,
                ),
                ft.Container(height=12),
                ft.Text("All Purchase Orders", size=13, color=TEXT_SECONDARY),
                ft.Container(height=8),
                po_table,
            ])),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )