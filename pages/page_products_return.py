#----------- Library ------------

import flet as ft
from datetime import datetime
from pymongo import MongoClient
import random

#-----------Own Defined Functions ----------

from ui.theme import (
    COLOR_DANGER,
    COLOR_SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from ui.components import (
    build_card,
    build_page_header,
    build_data_table,
    build_action_button,
)

#--------Database------------------------

client = MongoClient("mongodb://localhost:27017/")
db = client["inventory"]

#----------Collection-----------

products_col = db["products"]
products_return_col = db["products_return"]

#----------Button-----------------------

def return_product_button(product_id):
    product = products_col.find_one({"product_id": product_id})
    if not product:
        return
    product.pop("_id", None)
    product["status"] = "Processing"
    product["return_id"] = generate_return_id()
    products_return_col.insert_one(product)
    products_col.delete_one({"product_id": product_id})


def cancell_return_button(product_id):
    product = products_return_col.find_one({"product_id": product_id})
    if not product:
        return
    product.pop("_id", None)
    product.pop("status", None)
    product.pop("return_id", None)
    products_col.insert_one(product)
    products_return_col.delete_one({"product_id": product_id})


#-------------Return ID----------------------

def generate_return_id():
    now = datetime.now()
    base = now.strftime("%d%m%Y%H%M%S") + f"{int(now.microsecond/1000):03d}"
    return base + str(random.randint(100, 999))

#-------------Page Layout-------------------


def build_products_return_page(flet_page: ft.Page):

    show_status = {"value": False}
    main_container = ft.Column()

    product_table_rows = []

    def load_products():
        product_table_rows.clear()
        for product in products_col.find():
            product_table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(product.get("product_id", "")), color=TEXT_SECONDARY, size=12)),
                        ft.DataCell(ft.Text(product.get("name", ""), color=TEXT_PRIMARY, size=13)),
                        ft.DataCell(ft.Text(product.get("category_id", ""), color=TEXT_SECONDARY, size=12)),
                        ft.DataCell(ft.Text(str(product.get("current_stock", "")), color=TEXT_SECONDARY, size=13)),
                        ft.DataCell(ft.Text(f'₹{product.get("selling_price", ""):,.2f}', color=TEXT_PRIMARY, size=13)),
                        ft.DataCell(ft.Text(f'₹{product.get("cost_price", ""):,.2f}', color=TEXT_PRIMARY, size=13)),
                        ft.DataCell(ft.Text(product.get("supplier_id", ""), color=TEXT_SECONDARY, size=12)),
                        ft.DataCell(
                            ft.IconButton(
                                ft.Icons.ASSIGNMENT_RETURN_SHARP,
                                icon_color=COLOR_DANGER,
                                icon_size=16,
                                tooltip="Return",
                                on_click=lambda e, pid=product["product_id"]: handle_return(pid),
                            )
                        ),
                    ]
                )
            )
        flet_page.update()

    def handle_return(product_id):
        return_product_button(product_id)
        load_products()

    def load_status():
        status_rows.clear()
        for product in products_return_col.find():
            status_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(product.get("product_id", "")), color=TEXT_SECONDARY, size=12)),
                        ft.DataCell(ft.Text(product.get("name", ""), color=TEXT_PRIMARY, size=13)),
                        ft.DataCell(ft.Text(product.get("category_id", ""), color=TEXT_SECONDARY, size=12)),
                        ft.DataCell(ft.Text(str(product.get("current_stock", "")), color=TEXT_SECONDARY, size=13)),
                        ft.DataCell(ft.Text(f'₹{product.get("selling_price", ""):,.2f}', color=TEXT_PRIMARY, size=13)),
                        ft.DataCell(ft.Text(product.get("supplier_id", ""), color=TEXT_SECONDARY, size=12)),
                        ft.DataCell(ft.Text(product.get("status", ""), color=COLOR_DANGER, size=12)),
                        ft.DataCell(ft.Text(product.get("return_id",""), color=COLOR_SUCCESS, size=12)),
                        ft.DataCell(
                            ft.IconButton(
                                ft.Icons.CANCEL_SCHEDULE_SEND_ROUNDED,
                                icon_color=COLOR_DANGER,
                                icon_size=16,
                                tooltip="Cancel Return",
                                on_click=lambda e, pid=product["product_id"]: (cancell_return_button(pid), load_status()),
                            )
                        )
                    ]
                )
            )
        flet_page.update()

    def open_status():
        show_status["value"] = True
        refresh_view()

    def go_back():
        show_status["value"] = False
        refresh_view()

    def refresh_view():
        main_container.controls.clear()
        if show_status["value"]:
            main_container.controls.append(
                ft.Column(
                    [
                        build_page_header(
                            header_title="Status",
                            header_subtitle="Product return status",
                            header_icon=ft.Icons.CIRCLE_NOTIFICATIONS_SHARP,
                            action_buttons=[
                                build_action_button("Back", ft.Icons.ARROW_BACK, on_click_handler=lambda e: go_back())
                            ],
                        ),
                        ft.Container(height=20),
                        status_card,
                    ],
                    expand=True,
                )
            )
            load_status()
        else:
            main_container.controls.append(products_table_card)
            load_products()
        flet_page.update()

    products_table_card = build_card(
        ft.Column(
            [
                ft.Container(height=12),
                ft.Column(
                    [
                        build_data_table(
                            column_labels=[
                                "Product ID",
                                "Name",
                                "Category",
                                "Stock",
                                "Selling Price",
                                "Cost Price",
                                "Supplier",
                                "Actions",
                            ],
                            table_rows=product_table_rows,
                        )
                    ],
                    scroll=ft.ScrollMode.ADAPTIVE,
                ),
            ],
            spacing=0,
        )
    )

    status_rows = []

    status_card = build_card(
        ft.Column(
            [
                ft.Container(height=12),
                ft.Column(
                    [
                        build_data_table(
                            column_labels=[
                                "ID",
                                "Name",
                                "Category",
                                "Stock",
                                "Price",
                                "Supplier",
                                "Status",
                                "Return ID",
                                "Action",
                            ],
                            table_rows=status_rows,
                        )
                    ],
                    scroll=ft.ScrollMode.ADAPTIVE,
                ),
            ],
            spacing=0,
        )
    )

    refresh_view()

    return ft.Column(
        [
            build_page_header(
                header_title="Products Return",
                header_subtitle="Product return",
                header_icon=ft.Icons.ASSIGNMENT_RETURN_SHARP,
                action_buttons=[
                    build_action_button(
                        "Status",
                        ft.Icons.CIRCLE_NOTIFICATIONS_SHARP,
                        on_click_handler=lambda e: open_status()
                    )
                ],
            ),
            ft.Container(height=20),
            main_container,
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
    )