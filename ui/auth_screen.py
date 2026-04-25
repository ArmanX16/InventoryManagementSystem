import flet as ft
from pymongo import MongoClient
from datetime import datetime

from ui.theme import (
    ACCENT_PRIMARY,
    BACKGROUND_DARK,
    SURFACE_DARK,
    BORDER_DEFAULT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from ui.components import build_auth_text_field

# ---------------- MONGODB ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client["inventory"]
employees_col = db["employees"]
login_col = db["login"]

# ---------------- LOGIN ATTEMPTS ----------------
login_attempts = {"count": 0}


FEATURE_HIGHLIGHTS = [
    (ft.Icons.TRENDING_UP, "AI powered demand forecasting"),
    (ft.Icons.AUTORENEW, "Smart automatic reordering"),
    (ft.Icons.BAR_CHART, "Real time inventory analytics"),
    (ft.Icons.WARNING, "Proactive risk management"),
]


# ---------------- FEATURE PANEL (UNCHANGED UI) ----------------
def build_auth_feature_panel():
    feature_highlight_rows = [
        ft.Row(
            [
                ft.Container(
                    ft.Icon(feature_icon, color=ACCENT_PRIMARY, size=16),
                    bgcolor=ft.Colors.with_opacity(0.15, ACCENT_PRIMARY),
                    border_radius=8,
                    padding=6,
                ),
                ft.Text(feature_description, color=TEXT_SECONDARY, size=13),
            ],
            spacing=12,
        )
        for feature_icon, feature_description in FEATURE_HIGHLIGHTS
    ]

    return ft.Container(
        expand=True,
        bgcolor=SURFACE_DARK,
        border=ft.Border.only(right=ft.BorderSide(1, BORDER_DEFAULT)),
        content=ft.Column(
            [
                ft.Icon(ft.Icons.INVENTORY, color=ACCENT_PRIMARY, size=60),
                ft.Container(height=16),
                ft.Text("InventoryAI", size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("AI Powered Inventory Management", size=15, color=TEXT_SECONDARY),
                ft.Container(height=40),
                *feature_highlight_rows,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=14,
        ),
        padding=60,
    )


# ---------------- LOGIN FORM (UNCHANGED LOGIC) ----------------
def build_login_form(on_login_success_callback, on_navigate_to_forgot_callback):

    email = build_auth_text_field("Email Address", "you@company.com", ft.Icons.EMAIL)
    password = build_auth_text_field("Password", "••••••••", ft.Icons.LOCK, is_password_field=True)

    error = ft.Text("", color="red", size=12)

    def handle_login(e):
        if login_attempts["count"] >= 3:
            error.value = "Too many attempts!"
            e.page.update()
            return

        user = employees_col.find_one({"email": email.value})

        if not user:
            login_attempts["count"] += 1
            error.value = "Email not found"
            e.page.update()
            return

        if user["password"] != password.value:
            login_attempts["count"] += 1
            error.value = f"Wrong password ({3 - login_attempts['count']} left)"
            e.page.update()
            return

        login_attempts["count"] = 0

        # STORE LOGIN HISTORY
        login_col.insert_one({
            "employee_id": user.get("employee_id"),
            "email": user.get("email"),
            "login_time": datetime.now(),
        })

        session_data = {
            "employee_id": user.get("employee_id"),
            "name": user.get("name"),
            "role": user.get("role"),
            "email": user.get("email"),
        }

        on_login_success_callback(session_data)

    return ft.Column(
        [
            ft.Text("Welcome Back", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Sign in to your InventoryAI account", size=14, color=TEXT_SECONDARY),
            ft.Container(height=24),
            email,
            ft.Container(height=12),
            password,
            error,
            ft.Container(height=16),
            ft.ElevatedButton(
                "Sign In",
                icon=ft.Icons.LOGIN,
                on_click=handle_login,
                bgcolor=ACCENT_PRIMARY,
                color=TEXT_PRIMARY,
                width=340,
                height=46,
            ),
            ft.Container(height=16),
            ft.TextButton("Forgot Password?", on_click=on_navigate_to_forgot_callback),
            ft.TextButton(
                "Create Account",
                on_click=lambda e: e.page.open_create_account(e)
            ),
        ],
        spacing=0,
        width=340,
    )


# ---------------- FORGOT PASSWORD (SMALL POPUP WINDOW ADDED CLEANLY) ----------------
def forgot_dialog(page):
    email = build_auth_text_field("Email", "enter email", ft.Icons.EMAIL)
    new_pass = build_auth_text_field("New Password", "new password", ft.Icons.LOCK, is_password_field=True)
    msg = ft.Text(size=12)

    def close_dlg(e=None):
        dlg.open = False
        page.update()

    def update_pass(e):
        user = employees_col.find_one({"email": email.value})
        if not user:
            msg.value = "Email not found"
        else:
            employees_col.update_one(
                {"email": email.value},
                {"$set": {"password": new_pass.value}}
            )
            msg.value = "Password updated successfully"
        page.update()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Reset Password"),
        content=ft.Container(
            width=300,   # 👈 makes it SMALL WINDOW
            content=ft.Column(
                [
                    email,
                    ft.Container(height=10),
                    new_pass,
                    ft.Container(height=10),
                    msg
                ],
                tight=True
            ),
        ),
        actions=[
            ft.TextButton("Update", on_click=update_pass),
            ft.TextButton("Close", on_click=close_dlg),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    return dlg

# ---------------- ADD THIS NEW FUNCTION ----------------
def create_account_dialog(page):
    name = build_auth_text_field("Full Name", "enter full name", ft.Icons.PERSON)
    gender = build_auth_text_field("Gender", "Male / Female", ft.Icons.PERSON_OUTLINE)
    contact = build_auth_text_field("Contact", "phone number", ft.Icons.PHONE)
    dob = build_auth_text_field("DOB", "DD-MM-YYYY", ft.Icons.CALENDAR_MONTH)
    email = build_auth_text_field("Email", "enter email", ft.Icons.EMAIL)
    password = build_auth_text_field(
        "Password",
        "create password",
        ft.Icons.LOCK,
        is_password_field=True
    )
    salary = build_auth_text_field("Salary", "optional salary", ft.Icons.PAYMENTS)
    address = build_auth_text_field("Address", "enter address", ft.Icons.HOME)

    msg = ft.Text(size=12)

    def close_dlg(e=None):
        dlg.open = False
        page.update()

    # REPLACE ONLY THIS PART INSIDE create_account()

    def create_account(e):
        if not name.value or not email.value or not password.value:
            msg.value = "Name, Email and Password required"
            msg.color = "red"
            page.update()
            return

        existing = employees_col.find_one({"email": email.value})
        if existing:
            msg.value = "Email already exists"
            msg.color = "red"
            page.update()
            return

        last_emp = employees_col.find_one(
            sort=[("employee_id", -1)]
        )

        try:
            if last_emp and last_emp.get("employee_id"):
                last_num = int(
                    str(last_emp["employee_id"]).replace("emp", "")
                )
                new_emp_id = f"emp{last_num + 1}"
            else:
                new_emp_id = "emp1"
        except:
            new_emp_id = f"emp{int(datetime.now().timestamp())}"

        employees_col.insert_one({
            "name": name.value,
            "gender": gender.value if gender.value else "Unknown",
            "contact": contact.value if contact.value else "",
            "dob": dob.value if dob.value else "",
            "email": email.value,
            "password": password.value,
            "role": "Employee",
            "salary": int(salary.value) if salary.value and salary.value.isdigit() else 0,
            "address": address.value if address.value else "",
            "performance_score": 0,
            "total_sales": 0,
            "anomaly_flag": False,
            "employee_id": new_emp_id,
        })

        # SUCCESS MESSAGE
        msg.value = (
            f"Account created successfully ✅\n"
            f"Employee ID: {new_emp_id}\n"
            f"You may close this window now."
        )
        msg.color = "green"

        # OPTIONAL: clear fields after success
        name.value = ""
        gender.value = ""
        contact.value = ""
        dob.value = ""
        email.value = ""
        password.value = ""
        salary.value = ""
        address.value = ""

        page.update()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Create Account"),
        content=ft.Container(
            width=350,
            content=ft.Column(
                [
                    name,
                    ft.Container(height=8),
                    gender,
                    ft.Container(height=8),
                    contact,
                    ft.Container(height=8),
                    dob,
                    ft.Container(height=8),
                    email,
                    ft.Container(height=8),
                    password,
                    ft.Container(height=8),
                    salary,
                    ft.Container(height=8),
                    address,
                    ft.Container(height=10),
                    msg,
                ],
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        ),
        actions=[
            ft.TextButton("Create", on_click=create_account),
            ft.TextButton("Close", on_click=close_dlg),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    return dlg
# ---------------- MAIN AUTH ----------------
def show_auth_screen(flet_page: ft.Page, auth_sub_page, on_login_success_callback, on_navigate_callback):
    def open_forgot(e):
        dlg = forgot_dialog(flet_page)
        flet_page.dialog = dlg
        flet_page.overlay.append(dlg)
        dlg.open = True
        flet_page.update()

    def open_create_account(e):
        dlg = create_account_dialog(flet_page)
        flet_page.dialog = dlg
        flet_page.overlay.append(dlg)
        dlg.open = True
        flet_page.update()

    flet_page.open_create_account = open_create_account
    form = build_login_form(
        on_login_success_callback,
        open_forgot
    )

    form_container = ft.Container(
        width=480,
        content=ft.Column(
            [form],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=60,
    )

    flet_page.controls.clear()
    flet_page.add(
        ft.Container(
            expand=True,
            bgcolor=BACKGROUND_DARK,
            content=ft.Row(
                [
                    build_auth_feature_panel(),
                    form_container,
                ],
                spacing=0,
                expand=True,
            ),
        )
    )
    flet_page.update()
