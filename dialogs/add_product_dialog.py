import flet as ft
from datetime import datetime
from data.product_service import add_product
from data.database import categories_collection, suppliers_collection


def open_add_product_dialog(page: ft.Page, refresh_callback, categories=[], suppliers=[]):

    def load_categories():
        return [
            ft.dropdown.Option(
                key=str(cat.get("_id", "")),
                text=str(cat.get("name", "")),
            )
            for cat in categories
        ]

    def load_suppliers():
        return [
            ft.dropdown.Option(
                key=str(sup.get("_id", "")),
                text=str(sup.get("name", "")),
            )
            for sup in suppliers
        ]
           

    
               

    field_style = {
        "color": "white",
        "bgcolor": "#2a2a3e",
        "border_color": "#6C63FF",
        "focused_border_color": "#6C63FF",
        "label_style": ft.TextStyle(color="#aaaaaa"),
        "hint_style": ft.TextStyle(color="#888888"),
        "width": 280,
    }

    field_product_id     = ft.TextField(label="Product ID", **field_style)
    field_name           = ft.TextField(label="Product Name", **field_style)
    field_sku            = ft.TextField(label="SKU", **field_style)
    field_cost_price     = ft.TextField(label="Cost Price", **field_style, keyboard_type=ft.KeyboardType.NUMBER)
    field_selling_price  = ft.TextField(label="Selling Price", **field_style, keyboard_type=ft.KeyboardType.NUMBER)
    field_stock          = ft.TextField(label="Current Stock", **field_style, keyboard_type=ft.KeyboardType.NUMBER)
    field_safety_stock   = ft.TextField(label="Safety Stock", **field_style, keyboard_type=ft.KeyboardType.NUMBER)
    field_lead_time      = ft.TextField(label="Lead Time Days", **field_style, keyboard_type=ft.KeyboardType.NUMBER)
    field_reorder_point  = ft.TextField(label="Reorder Point", **field_style, keyboard_type=ft.KeyboardType.NUMBER)
    field_abc_class      = ft.TextField(label="ABC Class (A/B/C)", **field_style)
    field_xyz_class      = ft.TextField(label="XYZ Class (X/Y/Z)", **field_style)
    field_turnover_ratio = ft.TextField(label="Turnover Ratio", **field_style, keyboard_type=ft.KeyboardType.NUMBER)
    field_risk_score     = ft.TextField(label="Risk Score", **field_style, keyboard_type=ft.KeyboardType.NUMBER)

    field_category = ft.Dropdown(
        label="Category",
        width=280,
        options=load_categories(),
        color="white",
        bgcolor="#2a2a3e",
        border_color="#6C63FF",
        focused_border_color="#6C63FF",
        label_style=ft.TextStyle(color="#aaaaaa"),
    )

    field_supplier = ft.Dropdown(
        label="Supplier",
        width=280,
        options=load_suppliers(),
        color="white",
        bgcolor="#2a2a3e",
        border_color="#6C63FF",
        focused_border_color="#6C63FF",
        label_style=ft.TextStyle(color="#aaaaaa"),
    )

    error_text = ft.Text("", color="red", size=12)

    def to_int(val):
        try:
            return int(val)
        except:
            return 0

    def handle_submit(e):
        if not field_product_id.value or not field_name.value:
            error_text.value = " Product ID and Name are required."
            page.update()
            return

        new_product = {
            "product_id":     field_product_id.value.strip(),
            "name":           field_name.value.strip(),
            "sku":            field_sku.value.strip(),
            "category_id":    field_category.value,
            "supplier_id":    field_supplier.value,
            "cost_price":     to_int(field_cost_price.value),
            "selling_price":  to_int(field_selling_price.value),
            "current_stock":  to_int(field_stock.value),
            "safety_stock":   to_int(field_safety_stock.value),
            "lead_time_days": to_int(field_lead_time.value),
            "reorder_point":  to_int(field_reorder_point.value),
            "abc_class":      field_abc_class.value.strip(),
            "xyz_class":      field_xyz_class.value.strip(),
            "turnover_ratio": to_int(field_turnover_ratio.value),
            "risk_score":     to_int(field_risk_score.value),
            "created_at":     datetime.now(),
            "updated_at":     datetime.now(),
        }

        add_product(new_product)
        dialog.open = False
        page.update()
        refresh_callback()

    def close_dialog():
        dialog.open = False
        page.update()

    dialog = ft.AlertDialog(
        modal=True,
        open=False,
        title=ft.Text(
            "Add New Product",
            color="white",
            weight=ft.FontWeight.W_600,
            size=18,
        ),
        bgcolor="#1a1a2e",
        content=ft.Container(
            width=620,
            content=ft.Column(
                [
                    ft.Row([field_product_id, field_name], spacing=12),
                    ft.Row([field_sku, field_category], spacing=12),
                    ft.Row([field_supplier, field_cost_price], spacing=12),
                    ft.Row([field_selling_price, field_stock], spacing=12),
                    ft.Row([field_safety_stock, field_lead_time], spacing=12),
                    ft.Row([field_reorder_point, field_abc_class], spacing=12),
                    ft.Row([field_xyz_class, field_turnover_ratio], spacing=12),
                    ft.Row([field_risk_score], spacing=12),
                    error_text,
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                height=420,
            ),
        ),
        actions=[
            ft.TextButton(
                "Cancel",
                on_click=lambda e: close_dialog(),
                style=ft.ButtonStyle(color="#888888"),
            ),
            ft.ElevatedButton(
                "Add Product",
                bgcolor="#6C63FF",
                color="white",
                on_click=handle_submit,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    if dialog not in page.overlay:
        page.overlay.append(dialog)
    dialog.open = True
    page.update()