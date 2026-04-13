import flet as ft
from ui.theme import (
    ACCENT_PRIMARY,
    COLOR_DANGER,
    COLOR_WARNING,
    COLOR_SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    SURFACE_DARK,
    BORDER_DEFAULT,
)
from ui.components import (
    build_card,
    build_stat_card,
    build_page_header,
    build_data_table,
    build_action_button,
)
from data.product_service import get_all_products
from dialogs.add_product_dialog import open_add_product_dialog

# 🔥 CACHE (VERY IMPORTANT)
_cached_products = None


def build_products_page(
    flet_page: ft.Page,
    filtered_products=None,
    search_value="",
    selected_category="All Categories",
):

    from data.database import categories_collection, suppliers_collection

    db_categories = list(categories_collection.find({}, {"name": 1, "category_id": 1}).limit(50))
    db_suppliers = list(suppliers_collection.find({}, {"name": 1}).limit(50))

    global _cached_products

    # 🔥 LOAD ONLY ONCE
    if _cached_products is None:
        _cached_products = get_all_products()

    products = _cached_products if filtered_products is None else filtered_products

    def determine_stock_color(p):
        if int(p["current_stock"]) == 0:
            return COLOR_DANGER
        if int(p["current_stock"]) < int(p["reorder_point"]):
            return COLOR_WARNING
        return COLOR_SUCCESS

    table_column = ft.Column([])
    active_category = {"value": selected_category}

    # 🔥 FAST ROW BUILD
    def build_rows(product_list):
        return [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(p["product_id"], color=TEXT_SECONDARY, size=12)),
                    ft.DataCell(ft.Text(p["name"], color=TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(p["category_id"], color=TEXT_SECONDARY, size=12)),
                    ft.DataCell(
                        ft.Text(
                            str(p["current_stock"]),
                            color=determine_stock_color(p),
                            size=13,
                            weight=ft.FontWeight.W_600,
                        )
                    ),
                    ft.DataCell(ft.Text(f'₹{float(p["selling_price"]):,.2f}', color=TEXT_PRIMARY)),
                    ft.DataCell(ft.Text(p["supplier_id"], color=TEXT_SECONDARY)),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                ft.Icons.EDIT,
                                icon_color=ACCENT_PRIMARY,
                                on_click=lambda e, p=p: handle_edit_product(p),
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE,
                                icon_color=COLOR_DANGER,
                                on_click=lambda e, pid=p["product_id"]: handle_delete_product(pid),
                            ),
                        ])
                    ),
                ]
            )
            for p in product_list
        ]

    def refresh_table(product_list):
        table_column.controls.clear()
        table_column.controls.append(
            build_data_table(
                column_labels=[
                    "ID", "Name", "Category",
                    "Stock", "Price", "Supplier", "Actions",
                ],
                table_rows=build_rows(product_list),
            )
        )
        flet_page.update()

    # 🔥 SUPER FAST FILTER (NO DB CALL)
    def apply_filters(search_text, category):
        search_text = search_text.lower()

        filtered = _cached_products

        if search_text:
            filtered = [
                p for p in filtered
                if search_text in str(p.get("name", "")).lower()
                or search_text in str(p.get("product_id", "")).lower()
                or search_text in str(p.get("sku", "")).lower()
            ]

        if category != "All Categories":
            filtered = [
                p for p in filtered
                if p["category_id"].strip().lower() == category.strip().lower()
            ]

        refresh_table(filtered)

    def handle_search(e):
        apply_filters(e.control.value.strip(), active_category["value"])

    def handle_add_product(e):
        def after_add():
            global _cached_products
            _cached_products = get_all_products()  # 🔥 refresh cache
            refresh_table(_cached_products)

        open_add_product_dialog(
            flet_page,
            after_add,
            db_categories,
            db_suppliers,
        )

    def handle_delete_product(product_id):
        from data.product_service import delete_product
        delete_product(product_id)

        global _cached_products
        _cached_products = get_all_products()

        refresh_table(_cached_products)

    def handle_edit_product(product):
        from dialogs.edit_product_dialog import open_edit_product_dialog

        def after_edit():
            global _cached_products
            _cached_products = get_all_products()
            refresh_table(_cached_products)

        open_edit_product_dialog(
            flet_page,
            product,
            after_edit,
        )

    # 🔥 DYNAMIC CATEGORY FROM DB
    categories = ["All Categories"] + list({
        str(c.get("category_id", "")).strip()
        for c in db_categories if c.get("category_id")
    })

    category_buttons_row = ft.Row(spacing=8, wrap=True)

    def render_category_buttons():
        category_buttons_row.controls.clear()

        for cat in categories:
            is_active = active_category["value"] == cat

            def on_cat_click(e, label=cat):
                active_category["value"] = label
                render_category_buttons()
                apply_filters(search_field.value.strip(), label)

            category_buttons_row.controls.append(
                ft.ElevatedButton(
                    cat,
                    on_click=on_cat_click,
                    height=36,
                    style=ft.ButtonStyle(
                        bgcolor=ACCENT_PRIMARY if is_active else SURFACE_DARK,
                        color=TEXT_PRIMARY,
                        side=ft.BorderSide(
                            1,
                            ACCENT_PRIMARY if is_active else BORDER_DEFAULT,
                        ),
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                )
            )

        flet_page.update()

    search_field = ft.TextField(
        value=search_value,
        hint_text="Search by Name / ID / SKU...",
        prefix_icon=ft.Icons.SEARCH,
        bgcolor=SURFACE_DARK,
        border_color=BORDER_DEFAULT,
        focused_border_color=ACCENT_PRIMARY,
        color=TEXT_PRIMARY,
        hint_style=ft.TextStyle(color=TEXT_SECONDARY),
        height=42,
        expand=True,
        border_radius=10,
        on_change=handle_search,
    )

    render_category_buttons()
    refresh_table(products)

    products_table_card = build_card(
        ft.Column([
            ft.Row([search_field], spacing=12),
            ft.Container(height=8),
            category_buttons_row,
            ft.Container(height=12),
            table_column,
        ])
    )

    return ft.Column(
        [
            build_page_header(
                header_title="Products Management",
                header_subtitle="Manage your product catalog",
                header_icon=ft.Icons.INVENTORY,
                action_buttons=[
                    build_action_button(
                        "Add Product",
                        ft.Icons.ADD,
                        on_click_handler=handle_add_product,
                    )
                ],
            ),
            ft.Container(height=20),
            ft.ResponsiveRow(
                [
                    ft.Column(
                        [build_stat_card(ft.Icons.INVENTORY, "Total Products", len(products), None, ACCENT_PRIMARY)],
                        col={"xs": 6, "md": 3},
                    ),
                    ft.Column(
                        [build_stat_card(ft.Icons.CHECK_CIRCLE, "In Stock",
                                         sum(1 for p in products if int(p["current_stock"]) > 0),
                                         None, COLOR_SUCCESS)],
                        col={"xs": 6, "md": 3},
                    ),
                    ft.Column(
                        [build_stat_card(ft.Icons.WARNING, "Low Stock",
                                         sum(1 for p in products if 0 < int(p["current_stock"]) < int(p["reorder_point"])),
                                         None, COLOR_WARNING)],
                        col={"xs": 6, "md": 3},
                    ),
                    ft.Column(
                        [build_stat_card(ft.Icons.CANCEL, "Out of Stock",
                                         sum(1 for p in products if int(p["current_stock"]) == 0),
                                         None, COLOR_DANGER)],
                        col={"xs": 6, "md": 3},
                    ),
                ],
                spacing=16,
            ),
            ft.Container(height=20),
            products_table_card,
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )