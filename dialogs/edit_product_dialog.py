import flet as ft
from data.product_service import update_product


def open_edit_product_dialog(page, product, refresh_callback):

    name = ft.TextField(label="Product Name", value=product["name"])
    category = ft.TextField(label="Category", value=product["category_id"])
    stock = ft.TextField(label="Stock", value=str(product["current_stock"]))
    price = ft.TextField(label="Price", value=str(product["selling_price"]))
    reorder = ft.TextField(label="Reorder Level", value=str(product["reorder_point"]))
    supplier = ft.TextField(label="Supplier", value=product["supplier_id"])


    def save_product(e):

        updated_data = {
            "name": name.value,
            "category": category.value,
            "stock": int(stock.value),
            "price": float(price.value),
            "reorder": int(reorder.value),
            "supplier": supplier.value
        }

        update_product(product["product_id"], updated_data)

        dialog.open = False
        page.update()

        refresh_callback()


    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Edit Product"),
        content=ft.Column(
            [name, category, stock, price, reorder, supplier],
            scroll="auto"
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
            ft.ElevatedButton("Save Changes", on_click=save_product)
        ]
    )


    def close_dialog():
        dialog.open = False
        page.update()


    page.overlay.append(dialog)
    dialog.open = True
    page.update()