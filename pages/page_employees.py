import flet as ft
from pymongo import MongoClient

# ---------------- DB (UNCHANGED) ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client["inventory"]
collection = db["employees"]


def to_int(val):
    try:
        return int(val)
    except:
        return 0


def to_bool(val):
    return True if val == "True" else False


# ✅ IMPORTANT: MUST RETURN UI (not use page.add)
def build_employees_page(page: ft.Page):

    selected_id = {"value": None}

    # ---------------- INPUT FIELDS ----------------

    employee_id = ft.TextField(label="Employee ID")
    name = ft.TextField(label="Name")

    gender = ft.Dropdown(
        label="Gender",
        options=[
            ft.dropdown.Option("Male"),
            ft.dropdown.Option("Female"),
            ft.dropdown.Option("Other"),
        ],
    )

    contact = ft.TextField(label="Contact")
    dob = ft.TextField(label="DOB (DD-MM-YYYY)")

    email = ft.TextField(label="Email")
    password = ft.TextField(label="Password", password=True)

    role = ft.Dropdown(
        label="Role",
        options=[
            ft.dropdown.Option("Employee"),
            ft.dropdown.Option("Admin"),
            ft.dropdown.Option("Lead"),
            ft.dropdown.Option("Manager"),
            ft.dropdown.Option("Director"),
            ft.dropdown.Option("Expert"),
        ],
    )

    salary = ft.TextField(label="Salary")
    address = ft.TextField(label="Address")

    performance_score = ft.TextField(label="Performance Score")
    total_sales = ft.TextField(label="Total Sales")

    anomaly_flag = ft.Dropdown(
        label="Anomaly Flag",
        options=[
            ft.dropdown.Option("True"),
            ft.dropdown.Option("False"),
        ],
    )

    # ---------------- TABLE ----------------

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Employee ID")),
            ft.DataColumn(ft.Text("Name")),
            ft.DataColumn(ft.Text("Role")),
            ft.DataColumn(ft.Text("Salary")),
            ft.DataColumn(ft.Text("Score")),
        ],
        rows=[]
    )

    # ---------------- FUNCTIONS ----------------

    def clear_fields(e=None):
        selected_id["value"] = None

        for f in [
            employee_id, name, contact, dob, email,
            password, salary, address, performance_score, total_sales
        ]:
            f.value = ""

        gender.value = None
        role.value = None
        anomaly_flag.value = None

        page.update()

    def fill(emp):
        selected_id["value"] = emp["_id"]

        employee_id.value = emp.get("employee_id", "")
        name.value = emp.get("name", "")
        gender.value = emp.get("gender", "")
        contact.value = emp.get("contact", "")
        dob.value = emp.get("dob", "")
        email.value = emp.get("email", "")
        password.value = emp.get("password", "")
        role.value = emp.get("role", "")
        salary.value = str(emp.get("salary", ""))
        address.value = emp.get("address", "")
        performance_score.value = str(emp.get("performance_score", ""))
        total_sales.value = str(emp.get("total_sales", ""))
        anomaly_flag.value = "True" if emp.get("anomaly_flag") else "False"

        page.update()

    def load():
        table.rows.clear()

        for emp in collection.find():

            def click(e, emp_data=emp):
                fill(emp_data)

            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(emp.get("employee_id", "")), on_tap=click),
                        ft.DataCell(ft.Text(emp.get("name", ""))),
                        ft.DataCell(ft.Text(emp.get("role", ""))),
                        ft.DataCell(ft.Text(str(emp.get("salary", "")))),
                        ft.DataCell(ft.Text(str(emp.get("performance_score", "")))),
                    ]
                )
            )

        page.update()

    def add_emp(e):
        data = {
            "employee_id": employee_id.value,
            "name": name.value,
            "gender": gender.value,
            "contact": contact.value,
            "dob": dob.value,
            "email": email.value,
            "password": password.value,
            "role": role.value,
            "salary": to_int(salary.value),
            "address": address.value,
            "performance_score": to_int(performance_score.value),
            "total_sales": to_int(total_sales.value),
            "anomaly_flag": to_bool(anomaly_flag.value),
        }

        collection.insert_one(data)
        clear_fields()
        load()

    def update_emp(e):
        if not selected_id["value"]:
            return

        collection.update_one(
            {"_id": selected_id["value"]},
            {"$set": {
                "employee_id": employee_id.value,
                "name": name.value,
                "gender": gender.value,
                "contact": contact.value,
                "dob": dob.value,
                "email": email.value,
                "password": password.value,
                "role": role.value,
                "salary": to_int(salary.value),
                "address": address.value,
                "performance_score": to_int(performance_score.value),
                "total_sales": to_int(total_sales.value),
                "anomaly_flag": to_bool(anomaly_flag.value),
            }}
        )

        clear_fields()
        load()

    def delete_emp(e):
        if not selected_id["value"]:
            return

        collection.delete_one({"_id": selected_id["value"]})
        clear_fields()
        load()

    # ---------------- UI (WHITE BACKGROUND) ----------------

    layout = ft.Container(
        bgcolor="white",   # ✅ WHITE BACKGROUND
        expand=True,
        padding=20,
        content=ft.Column(
            [
                ft.Text("Employee Management System", size=28, weight="bold"),

                ft.Row([employee_id, name, gender]),
                ft.Row([contact, dob, email]),
                ft.Row([password, role, salary]),
                ft.Row([performance_score, total_sales, anomaly_flag]),
                address,

                ft.Row([
                    ft.ElevatedButton("Add", on_click=add_emp),
                    ft.ElevatedButton("Update", on_click=update_emp),
                    ft.ElevatedButton("Delete", on_click=delete_emp),
                    ft.ElevatedButton("Clear", on_click=clear_fields),
                ]),

                table
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    )

    # load AFTER UI created
    load()

    return layout