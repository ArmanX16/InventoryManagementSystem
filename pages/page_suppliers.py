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
    build_card, build_page_header, build_stat_card,
)

suppliers_col = db["suppliers"]
products_col = db["products"]
po_col = db["purchase_orders"]


def build_suppliers_page(flet_page: ft.Page):

    selected_id = {"value": None}
    selected_po = {"value": None}

    # ── FIELD STYLE ───────────────────────────────────────
    fs = {
        "color": TEXT_PRIMARY,
        "bgcolor": SURFACE_DARK,
        "border_color": BORDER_DEFAULT,
        "focused_border_color": ACCENT_PRIMARY,
        "label_style": ft.TextStyle(color=TEXT_SECONDARY),
        "width": 250,
    }

    # ── SUPPLIER FORM FIELDS ──────────────────────────────
    f_name        = ft.TextField(label="Supplier Name", **fs)
    f_contact     = ft.TextField(label="Contact", **fs)
    f_email       = ft.TextField(label="Email", **fs)
    f_address     = ft.TextField(label="Address", **fs)
    f_lead_time   = ft.TextField(label="Avg Lead Time (days)", **fs, keyboard_type=ft.KeyboardType.NUMBER)
    f_reliability = ft.TextField(label="Reliability Score (1-10)", **fs, keyboard_type=ft.KeyboardType.NUMBER)

    error_text = ft.Text("", color="red", size=12)
    table_column = ft.Column([])

    # ── BUILD SUPPLIER ROWS ───────────────────────────────
    def build_supplier_rows(sup_list):
        rows = []
        for s in sup_list:
            def on_tap(e, data=s):
                fill_fields(data)

            rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(s.get("_id", "")), color=TEXT_SECONDARY, size=12), on_tap=on_tap),
                    ft.DataCell(ft.Text(s.get("name", ""), color=TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(str(s.get("contact", "")), color=TEXT_SECONDARY, size=12)),
                    ft.DataCell(ft.Text(str(s.get("email", "")), color=TEXT_SECONDARY, size=12)),
                    ft.DataCell(ft.Text(str(s.get("avg_lead_time", "")), color=ACCENT_PRIMARY, size=12)),
                    ft.DataCell(ft.Text(str(s.get("reliability_score", "")), color=COLOR_WARNING, size=12)),
                    ft.DataCell(ft.Row([
                        ft.IconButton(ft.Icons.EDIT, icon_color=ACCENT_PRIMARY, on_click=lambda e, data=s: fill_fields(data)),
                        ft.IconButton(ft.Icons.DELETE, icon_color=COLOR_DANGER, on_click=lambda e, sid=s["_id"]: delete_supplier(sid)),
                    ])),
                ]
            ))
        return rows

    # ── REFRESH SUPPLIER TABLE ────────────────────────────
    def refresh_table():
        from ui.components import build_data_table
        sups = list(suppliers_col.find().limit(100))
        table_column.controls.clear()
        table_column.controls.append(
            build_data_table(
                column_labels=["ID", "Name", "Contact", "Email", "Lead Time", "Reliability", "Actions"],
                table_rows=build_supplier_rows(sups),
            )
        )
        flet_page.update()

    # ── FILL FIELDS ───────────────────────────────────────
    def fill_fields(s):
        selected_id["value"] = s["_id"]
        f_name.value        = s.get("name", "")
        f_contact.value     = str(s.get("contact", ""))
        f_email.value       = s.get("email", "")
        f_address.value     = s.get("address", "")
        f_lead_time.value   = str(s.get("avg_lead_time", ""))
        f_reliability.value = str(s.get("reliability_score", ""))
        error_text.value    = ""
        flet_page.update()

    # ── CLEAR FIELDS ──────────────────────────────────────
    def clear_fields(e=None):
        selected_id["value"] = None
        for f in [f_name, f_contact, f_email, f_address, f_lead_time, f_reliability]:
            f.value = ""
        error_text.value = ""
        flet_page.update()

    # ── ADD SUPPLIER ──────────────────────────────────────
    def add_supplier(e):
        if not f_name.value:
            error_text.value = "⚠ Supplier name is required."
            flet_page.update()
            return
        suppliers_col.insert_one({
            "name":              f_name.value.strip(),
            "contact":           f_contact.value.strip(),
            "email":             f_email.value.strip(),
            "address":           f_address.value.strip(),
            "avg_lead_time":     int(f_lead_time.value or 7),
            "reliability_score": int(f_reliability.value or 5),
            "created_at":        datetime.utcnow(),
        })
        error_text.value = "✅ Supplier added!"
        clear_fields()
        refresh_table()

    # ── UPDATE SUPPLIER ───────────────────────────────────
    def update_supplier(e):
        if not selected_id["value"]:
            error_text.value = "⚠ Select a supplier first."
            flet_page.update()
            return
        suppliers_col.update_one(
            {"_id": selected_id["value"]},
            {"$set": {
                "name":              f_name.value.strip(),
                "contact":           f_contact.value.strip(),
                "email":             f_email.value.strip(),
                "address":           f_address.value.strip(),
                "avg_lead_time":     int(f_lead_time.value or 7),
                "reliability_score": int(f_reliability.value or 5),
            }}
        )
        error_text.value = "✅ Supplier updated!"
        clear_fields()
        refresh_table()

    # ── DELETE SUPPLIER ───────────────────────────────────
    def delete_supplier(supplier_id):
        suppliers_col.delete_one({"_id": supplier_id})
        clear_fields()
        refresh_table()

    # ── SUPPLIER APPROVAL ─────────────────────────────────
    po_id_f       = ft.TextField(label="PO ID", width=180, disabled=True, **{k: v for k, v in fs.items() if k != "width"})
    product_id_f  = ft.TextField(label="Product ID", width=180, disabled=True, **{k: v for k, v in fs.items() if k != "width"})
    supplier_id_f = ft.TextField(label="Supplier ID", width=180, disabled=True, **{k: v for k, v in fs.items() if k != "width"})
    quantity_f    = ft.TextField(label="Delivered Qty", width=180, keyboard_type=ft.KeyboardType.NUMBER, **{k: v for k, v in fs.items() if k != "width"})

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
                po_id_f.value       = str(data["_id"])
                product_id_f.value  = data["product_id"]
                supplier_id_f.value = data["supplier_id"]
                quantity_f.value    = str(data["quantity"])
                status_dd.value     = None
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
    refresh_table()
    load_po_table()

    total_suppliers = suppliers_col.count_documents({})
    total_pos = po_col.count_documents({})

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
                ft.Column([build_stat_card(ft.Icons.LOCAL_SHIPPING, "Total Suppliers", total_suppliers, None, ACCENT_PRIMARY)], col={"xs": 6, "md": 3}),
                ft.Column([build_stat_card(ft.Icons.SHOPPING_CART, "Total POs", total_pos, None, COLOR_SUCCESS)], col={"xs": 6, "md": 3}),
                ft.Column([build_stat_card(ft.Icons.ACCESS_TIME, "Avg Lead Time", "8 days", None, ACCENT_SECONDARY)], col={"xs": 6, "md": 3}),
                ft.Column([build_stat_card(ft.Icons.STAR, "Avg Reliability", "7.5", None, COLOR_WARNING)], col={"xs": 6, "md": 3}),
            ], spacing=16),

            ft.Container(height=20),

            # Supplier CRUD Form
            build_card(ft.Column([
                ft.Text("Supplier Form", size=15, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ft.Container(height=8),
                ft.Row([f_name, f_contact, f_email], spacing=12),
                ft.Row([f_address, f_lead_time, f_reliability], spacing=12),
                ft.Container(height=8),
                error_text,
                ft.Row([
                    ft.ElevatedButton("Add", bgcolor=COLOR_SUCCESS, color="white", on_click=add_supplier),
                    ft.ElevatedButton("Update", bgcolor=ACCENT_PRIMARY, color="white", on_click=update_supplier),
                    ft.ElevatedButton("Delete", bgcolor=COLOR_DANGER, color="white", on_click=lambda e: delete_supplier(selected_id["value"]) if selected_id["value"] else None),
                    ft.ElevatedButton("Clear", on_click=clear_fields),
                ], spacing=12),
            ], spacing=10)),

            ft.Container(height=16),

            # Suppliers Table
            build_card(ft.Column([
                ft.Text("All Suppliers", size=15, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ft.Container(height=12),
                table_column,
            ])),

            ft.Container(height=20),

            # Supplier Approval
            build_card(ft.Column([
                ft.Text("Supplier Order Approval", size=15, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ft.Container(height=12),
                ft.Row([po_id_f, product_id_f, supplier_id_f], spacing=12),
                ft.Row([quantity_f, status_dd], spacing=12),
                ft.Container(height=8),
                ft.ElevatedButton("Update Order", bgcolor=ACCENT_PRIMARY, color="white", on_click=update_po),
                ft.Container(height=12),
                po_table,
            ])),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )