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


# ---------------- PAGE REGISTRY ----------------
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


# ---------------- ROLE ACCESS ----------------
ROLE_ACCESS = {
    "Admin": list(PAGE_BUILDER_REGISTRY.keys()),
    "Lead": list(PAGE_BUILDER_REGISTRY.keys()),

    "Manager": [
        "dashboard",
        "products",
        "categories",
        "Billing",
        "suppliers",
        "forecast",
        "analytics",
        "purchase_orders",
    ],

    "Employee": [
        "dashboard",
        "products",
        "sales",
    ],
}


# ---------------- SESSION CACHE ----------------
user_session_cache = {}


def set_session(page, key, value):
    user_session_cache[key] = value
    try:
        page.session.set(key, value)
    except:
        pass


def get_session(page, key):
    try:
        val = page.session.get(key)
        if val:
            return val
    except:
        pass
    return user_session_cache.get(key)


def remove_session(page, key):
    user_session_cache.pop(key, None)
    try:
        page.session.remove(key)
    except:
        pass


# ---------------- MAIN ----------------
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
        "active_route": "dashboard",
    }

    # ---------------- APP ----------------
    def rebuild_app_shell_with_route(new_active_route):

        user = get_session(flet_page, "user")

        if not user:
            navigate_to_auth_screen("login")
            return

        role = user.get("role", "Employee")
        allowed_pages = ROLE_ACCESS.get(role, [])

        # restrict invalid routes
        if new_active_route not in allowed_pages:
            new_active_route = "dashboard"

        application_state["active_route"] = new_active_route

        active_page_builder_function = PAGE_BUILDER_REGISTRY.get(
            new_active_route,
            build_dashboard_page,
        )

        # ✅ ONLY CHANGE: PASS SESSION DATA
        sidebar_widget = build_sidebar_navigation(
            currently_active_route_key=new_active_route,
            on_navigation_item_click_callback=rebuild_app_shell_with_route,
            on_logout_click_callback=lambda e: logout(),
            user_data=user,

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

    # ---------------- LOGOUT ----------------
    def logout():
        remove_session(flet_page, "user")
        navigate_to_auth_screen("login")

    # ---------------- AUTH ----------------
    def navigate_to_auth_screen(auth_sub_page_key):

        def handle_auth_success(session_data):
            set_session(flet_page, "user", session_data)

            # instant load
            rebuild_app_shell_with_route("dashboard")

        show_auth_screen(
            flet_page=flet_page,
            auth_sub_page=auth_sub_page_key,
            on_login_success_callback=handle_auth_success,
            on_navigate_callback=lambda x: None,
        )

    # ---------------- START ----------------
    user = get_session(flet_page, "user")

    if user:
        rebuild_app_shell_with_route("dashboard")
    else:
        navigate_to_auth_screen("login")


# ---------------- RUN ----------------
if __name__ == "__main__":
    ft.run(main)