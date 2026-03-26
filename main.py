import flet as ft

from ui.theme import BACKGROUND_DARK
from ui.shell_layout import build_sidebar_navigation, build_topbar
from ui.auth_screen import show_auth_screen


from pages.data_cleaning_visualization import build_data_cleaning_visualization_page

from pages.page_dashboard import build_dashboard_page
from pages.page_products import build_products_page
from pages.page_categories import build_categories_page
from pages.page_sales import build_sales_page
from pages.page_suppliers import build_suppliers_page
from pages.page_employees import build_employees_page
from pages.page_forecast import build_forecast_page
from pages.page_reorder import build_reorder_page
from pages.page_risk import build_risk_page
from pages.page_analytics import build_analytics_page

from pages.page_purchase_orders import build_purchase_orders_page
from pages.page_admin import build_admin_page

PAGE_BUILDER_REGISTRY = {
    "dashboard": build_dashboard_page,
    "products": build_products_page,
    "categories": build_categories_page,
    "sales": build_sales_page,
    "suppliers": build_suppliers_page,
    "employees": build_employees_page,
    "forecast": build_forecast_page,
    "reorder": build_reorder_page,
    "risk": build_risk_page,
    "data_cleaning": build_data_cleaning_visualization_page,
    "analytics": build_analytics_page,
    "purchase_orders": build_purchase_orders_page,
    "admin": build_admin_page,


}



def main(flet_page: ft.Page):
    flet_page.title = "Inventory Management System"
    flet_page.bgcolor = BACKGROUND_DARK
    flet_page.padding = 0

    flet_page.window.width = 1280
    flet_page.window.height = 820
    flet_page.window.min_width = 800
    flet_page.window.min_height = 600


    flet_page.fonts = {
        "Inter": (
            "https://fonts.gstatic.com/s/inter/v13/"
            "UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2"
        )
    }

    flet_page.theme = ft.Theme(font_family="Inter")
    flet_page.dark_theme = ft.Theme(font_family="Inter")

    application_state = {
        "current_screen": "auth",
        "auth_sub_page": "login",
        "active_route": "dashboard",
    }

    def rebuild_app_shell_with_route(new_active_route):

        application_state["active_route"] = new_active_route

        active_page_builder_function = PAGE_BUILDER_REGISTRY.get(
            new_active_route,
            build_dashboard_page,
        )

        sidebar_widget = build_sidebar_navigation(
            currently_active_route_key=new_active_route,
            on_navigation_item_click_callback=rebuild_app_shell_with_route,
            on_logout_click_callback=lambda e: navigate_to_auth_screen("login"),
        )


        topbar_widget = build_topbar(
            currently_active_route_key=new_active_route
        )

        active_page_content_widget = active_page_builder_function(flet_page)

        flet_page.controls.clear()
        flet_page.add(
            ft.Row(
                [
                    sidebar_widget,
                    ft.Column(
                        [
                            topbar_widget,
                            ft.Container(
                                content=active_page_content_widget,
                                expand=True,
                                padding=24,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            )
        )

        flet_page.update()

    def navigate_to_auth_screen(auth_sub_page_key):

        application_state["current_screen"] = "auth"
        application_state["auth_sub_page"] = auth_sub_page_key

        def handle_auth_success(e):
            application_state["current_screen"] = "app"
            application_state["active_route"] = "dashboard"
            rebuild_app_shell_with_route("dashboard")

        show_auth_screen(
            flet_page=flet_page,
            auth_sub_page=auth_sub_page_key,
            on_login_success_callback=handle_auth_success,
            on_navigate_callback=navigate_to_auth_screen,
        )

    navigate_to_auth_screen("login")

if __name__ == "__main__":
    ft.run(main)