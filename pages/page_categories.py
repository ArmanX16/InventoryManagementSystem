import flet as ft
from pymongo import MongoClient
from datetime import datetime
client = MongoClient("mongodb://localhost:27017/")
db = client["inventory"]


col = db["categories"]


def build_categories_page(flet_page: ft.Page):

    sel = {"id": None}

    id_f = ft.TextField(label="Category ID", width=250)
    name_f = ft.TextField(label="Category Name", width=350)
    desc_f = ft.TextField(label="Description", width=500, multiline=True)
    time_f = ft.TextField(label="Created At", width=250, disabled=True)
    search_f = ft.TextField(
        label="Search Category",
        hint_text="Search by ID, Name, or Description",
        width=500,
        prefix_icon=ft.Icons.SEARCH,
    )
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Name")),
            ft.DataColumn(ft.Text("Description")),
            ft.DataColumn(ft.Text("Created At")),
        ],
        rows=[],
        border=ft.border.all(1, "#cbd5e1"),
        border_radius=10,
    )

    def reset(e=None):
        sel["id"] = None
        id_f.value = ""
        name_f.value = ""
        desc_f.value = ""
        time_f.value = ""
        flet_page.update()

    def fill(d):
        sel["id"] = d["_id"]
        id_f.value = d["_id"]
        name_f.value = d.get("name", "")
        desc_f.value = d.get("description", "")
        time_f.value = str(d.get("created_at", ""))
        flet_page.update()

    def load(data=None):
        table.rows.clear()

        if data is None:
            search_text = search_f.value.strip()

            if search_text:
                records = list(
                    col.find(
                        {
                            "$or": [
                                {"_id": {"$regex": search_text, "$options": "i"}},
                                {"name": {"$regex": search_text, "$options": "i"}},
                                {"description": {"$regex": search_text, "$options": "i"}},
                            ]
                        }
                    ).limit(20)
                )
            else:
                records = list(col.find().limit(20))
        else:
            records = list(data)[:20]

        for d in records:
            def click(e, x=d):
                fill(x)

            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(d.get("_id", ""))), on_tap=click),
                        ft.DataCell(ft.Text(d.get("name", ""))),
                        ft.DataCell(ft.Text(d.get("description", ""))),
                        ft.DataCell(ft.Text(str(d.get("created_at", "")))),
                    ]
                )
            )

        flet_page.update()

    def search_data(e):
        load()
    def add(e):
        if not id_f.value:
            return
        if col.find_one({"_id": id_f.value}):
            return
        d = {
            "_id": id_f.value,
            "name": name_f.value,
            "description": desc_f.value,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
        }
        col.insert_one(d)
        reset()
        load()

    def update(e):
        if not sel["id"]:
            return
        col.update_one(
            {"_id": sel["id"]},
            {"$set": {"name": name_f.value, "description": desc_f.value}},
        )
        reset()
        load()

    def delete(e):
        if not sel["id"]:
            return
        col.delete_one({"_id": sel["id"]})
        reset()
        load()

    btn_add = ft.ElevatedButton("Add", bgcolor="#22c55e", color="white", on_click=add)
    btn_upd = ft.ElevatedButton("Update", bgcolor="#3b82f6", color="white", on_click=update)
    btn_del = ft.ElevatedButton("Delete", bgcolor="#ef4444", color="white", on_click=delete)
    btn_clr = ft.ElevatedButton("Clear", bgcolor="#64748b", color="white", on_click=reset)
    btn_search = ft.ElevatedButton(
        "Search",
        bgcolor="#8b5cf6",
        color="white",
        on_click=search_data
    )
    form = ft.Container(
        content=ft.Column(
            [
                ft.Text("Category Form", size=26, weight="bold"),
                id_f,
                name_f,
                desc_f,
                time_f,
                search_f,
                ft.Row(
                    [btn_add, btn_upd, btn_del, btn_clr, btn_search],
                    spacing=20
                ),
            ],
            spacing=15,
        ),
        padding=25,
        bgcolor="white",
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=15, color="#cbd5f5"),
    )

    grid = ft.Container(
        content=ft.Column(
            [
                ft.Text("All Categories", size=24, weight="bold"),
                table,
            ]
        ),
        padding=25,
        bgcolor="white",
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=15, color="#cbd5f5"),
    )

    load()

    return ft.Column(
        [
            ft.Text("Category Management", size=34, weight="bold", color="#1e293b"),
            form,
            grid,
        ],
        spacing=30,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )