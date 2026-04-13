import flet as ft
from datetime import datetime
from pymongo import ReturnDocument
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from data.database import db

products_col = db["products"]
customers_col = db["customers"]
sales_col = db["sales"]
invoices_col = db["invoices"]
counters_col = db["counters"]


def get_next_id(name, prefix, base):
    counter = counters_col.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    if counter["seq"] < base:
        counters_col.update_one({"_id": name}, {"$set": {"seq": base}})
        return f"{prefix}{base}"
    return f"{prefix}{counter['seq']}"


def update_product_stock(product_id, qty_sold):
    product = products_col.find_one({"product_id": product_id})
    if not product:
        return
    try:
        current = int(product.get("current_stock", 0))
    except:
        current = 0
    new_stock = current - qty_sold
    if new_stock < 0:
        new_stock = 0
    products_col.update_one(
        {"product_id": product_id},
        {"$set": {
            "current_stock": new_stock,
            "updated_at": datetime.utcnow()
        }}
    )


def build_sales_page(flet_page: ft.Page):

    cart = []
    selected_product = {}

    # ── INPUTS ────────────────────────────────────────────
    search = ft.TextField(
        label="Search Product",
        expand=True,
        color="white",
        bgcolor="#2a2a3e",
        border_color="#6C63FF",
        focused_border_color="#6C63FF",
        label_style=ft.TextStyle(color="#aaaaaa"),
    )
    customer_name = ft.TextField(
        label="Customer Name", width=250,
        color="white", bgcolor="#2a2a3e",
        border_color="#6C63FF",
        label_style=ft.TextStyle(color="#aaaaaa"),
    )
    customer_contact = ft.TextField(
        label="Contact", width=250,
        color="white", bgcolor="#2a2a3e",
        border_color="#6C63FF",
        label_style=ft.TextStyle(color="#aaaaaa"),
    )
    employee_id = ft.TextField(
        label="Employee ID", width=250,
        color="white", bgcolor="#2a2a3e",
        border_color="#6C63FF",
        label_style=ft.TextStyle(color="#aaaaaa"),
    )
    product_name = ft.TextField(
        label="Product", expand=True,
        read_only=True,
        color="white", bgcolor="#2a2a3e",
        border_color="#6C63FF",
        label_style=ft.TextStyle(color="#aaaaaa"),
    )
    price = ft.TextField(
        label="Price", width=120,
        color="white", bgcolor="#2a2a3e",
        border_color="#6C63FF",
        label_style=ft.TextStyle(color="#aaaaaa"),
    )
    qty = ft.TextField(
        label="Qty", width=80,
        value="1",
        color="white", bgcolor="#2a2a3e",
        border_color="#6C63FF",
        label_style=ft.TextStyle(color="#aaaaaa"),
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    discount = ft.TextField(
        label="Discount %", value="0", width=120,
        color="white", bgcolor="#2a2a3e",
        border_color="#6C63FF",
        label_style=ft.TextStyle(color="#aaaaaa"),
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    # ── TABLES ────────────────────────────────────────────
    product_table = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(ft.Text("Name", color="white")),
            ft.DataColumn(ft.Text("Price", color="white")),
            ft.DataColumn(ft.Text("Stock", color="white")),
        ],
        rows=[]
    )

    cart_table = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(ft.Text("Name", color="white")),
            ft.DataColumn(ft.Text("Qty", color="white")),
            ft.DataColumn(ft.Text("Total", color="white")),
        ],
        rows=[]
    )

    total_text = ft.Text("Total: ₹0", color="white", size=14)
    net_text = ft.Text("Net: ₹0", weight=ft.FontWeight.BOLD, color="#6C63FF", size=16)
    error_text = ft.Text("", color="red", size=12)

    # ── LOAD PRODUCTS ─────────────────────────────────────
    def load_products(e=None):
        product_table.rows.clear()
        query = search.value.lower() if search.value else ""

        for p in products_col.find().limit(100):
            if query and query not in p.get("name", "").lower():
                continue

            def select(ev, prod=p):
                selected_product.clear()
                selected_product.update(prod)
                product_name.value = prod["name"]
                price.value = str(prod["selling_price"])
                qty.value = "1"
                flet_page.update()

            try:
                stock = int(p.get("current_stock", 0))
            except:
                stock = 0

            stock_color = "#ef4444" if stock == 0 else "#f59e0b" if stock < 20 else "#22c55e"

            product_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p["name"], color="white", size=12), on_tap=select),
                    ft.DataCell(ft.Text(f"₹{p['selling_price']}", color="white", size=12)),
                    ft.DataCell(ft.Text(str(stock), color=stock_color, size=12)),
                ])
            )
        flet_page.update()

    # ── REFRESH CART ──────────────────────────────────────
    def refresh_cart():
        cart_table.rows.clear()
        total = 0

        for item in cart:
            subtotal = item["price"] * item["qty"]
            total += subtotal
            cart_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(item["name"], color="white", size=12)),
                    ft.DataCell(ft.Text(str(item["qty"]), color="white", size=12)),
                    ft.DataCell(ft.Text(f"₹{subtotal}", color="white", size=12)),
                ])
            )

        disc = float(discount.value or 0)
        net = total - (total * disc / 100)
        total_text.value = f"Total: ₹{total:,.2f}"
        net_text.value = f"Net: ₹{net:,.2f}"
        flet_page.update()

    # ── ADD TO CART ───────────────────────────────────────
    def add_cart(e):
        if not selected_product:
            error_text.value = "⚠ Select a product first."
            flet_page.update()
            return
        try:
            q = int(qty.value)
        except:
            error_text.value = "⚠ Enter valid quantity."
            flet_page.update()
            return

        try:
            stock = int(selected_product.get("current_stock", 0))
        except:
            stock = 0

        if q > stock:
            error_text.value = "⚠ Not enough stock!"
            flet_page.update()
            return

        cart.append({
            "product_id": selected_product["product_id"],
            "name": selected_product["name"],
            "price": float(price.value),
            "qty": q
        })
        error_text.value = ""
        refresh_cart()

    def clear_cart(e):
        cart.clear()
        refresh_cart()

    # ── GENERATE BILL ─────────────────────────────────────
    def save_bill(e):
        if not cart:
            error_text.value = "⚠ Cart is empty."
            flet_page.update()
            return
        if not customer_name.value or not employee_id.value:
            error_text.value = "⚠ Customer name and Employee ID required."
            flet_page.update()
            return

        invoice_id = get_next_id("invoice", "INV", 11000)
        invoice_number = f"INV{int(datetime.now().timestamp())}"
        customer_id = get_next_id("customer", "C", 501)

        customers_col.insert_one({
            "customer_id": customer_id,
            "name": customer_name.value,
            "contact": customer_contact.value,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
        })

        total = sum(i["price"] * i["qty"] for i in cart)
        disc = float(discount.value or 0)
        net = total - (total * disc / 100)

        for item in cart:
            sales_col.insert_one({
                "sale_id": get_next_id("sale", "s", 35136),
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "product_id": item["product_id"],
                "customer_id": customer_id,
                "employee_id": employee_id.value,
                "qty": item["qty"],
                "total": item["price"] * item["qty"],
                "date": datetime.now().strftime("%Y-%m-%d")
            })
            update_product_stock(item["product_id"], item["qty"])

        invoices_col.insert_one({
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "customer_id": customer_id,
            "employee_id": employee_id.value,
            "items": cart.copy(),
            "total": total,
            "discount": disc,
            "net": net,
            "created_at": datetime.utcnow()
        })

        generate_pdf(
            invoice_number, total, disc, net,
            customer_name.value, customer_contact.value,
            employee_id.value, cart.copy()
        )

        error_text.value = f"✅ Bill generated! Invoice: {invoice_number}"
        cart.clear()
        customer_name.value = ""
        customer_contact.value = ""
        employee_id.value = ""
        refresh_cart()
        flet_page.update()

    # ── PDF ───────────────────────────────────────────────
    def generate_pdf(invoice, total, disc, net, cname, contact, emp, items):
        try:
            doc = SimpleDocTemplate(f"{invoice}.pdf")
            styles = getSampleStyleSheet()
            elements = []
            elements.append(Paragraph(f"Invoice: {invoice}", styles["Title"]))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"Customer: {cname}", styles["Normal"]))
            elements.append(Paragraph(f"Contact: {contact}", styles["Normal"]))
            elements.append(Paragraph(f"Employee: {emp}", styles["Normal"]))
            elements.append(Spacer(1, 10))
            for item in items:
                elements.append(Paragraph(
                    f"{item['name']} - Qty: {item['qty']} x Price: {item['price']}",
                    styles["Normal"]
                ))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"Total: {total}", styles["Normal"]))
            elements.append(Paragraph(f"Discount: {disc}%", styles["Normal"]))
            elements.append(Paragraph(f"Net: {net}", styles["Normal"]))
            doc.build(elements)
        except Exception as ex:
            print(f"PDF error: {ex}")

    # ── INITIAL LOAD ──────────────────────────────────────
    load_products(None)

    # ── RETURN PAGE ───────────────────────────────────────
    return ft.Column(
        [
            ft.Text(
                "Smart Billing System",
                size=28,
                weight=ft.FontWeight.BOLD,
                color="white",
            ),
            ft.Container(height=16),
            ft.Row(
                [
                    # LEFT — Product Search
                    ft.Container(
                        expand=2,
                        content=ft.Column([
                            ft.Text("Products", size=16, weight=ft.FontWeight.W_600, color="white"),
                            ft.Row([
                                search,
                                ft.ElevatedButton(
                                    "Search",
                                    on_click=load_products,
                                    bgcolor="#6C63FF",
                                    color="white",
                                ),
                            ], spacing=8),
                            ft.Container(
                                content=product_table,
                                bgcolor="#1e1e2e",
                                border_radius=10,
                                padding=10,
                            ),
                        ], spacing=10),
                        padding=10,
                        bgcolor="#1a1a2e",
                        border_radius=12,
                    ),

                    # MIDDLE — Cart & Customer
                    ft.Container(
                        expand=2,
                        content=ft.Column([
                            ft.Text("Cart & Customer", size=16, weight=ft.FontWeight.W_600, color="white"),
                            ft.Row([customer_name, customer_contact], spacing=8),
                            ft.Container(
                                content=cart_table,
                                bgcolor="#1e1e2e",
                                border_radius=10,
                                padding=10,
                                height=200,
                            ),
                            ft.Row([product_name, price, qty], spacing=8),
                            ft.Row([
                                ft.ElevatedButton("Add to Cart", bgcolor="#22c55e", color="white", on_click=add_cart),
                                ft.ElevatedButton("Clear Cart", bgcolor="#64748b", color="white", on_click=clear_cart),
                            ], spacing=8),
                            error_text,
                        ], spacing=10),
                        padding=10,
                        bgcolor="#1a1a2e",
                        border_radius=12,
                    ),

                    # RIGHT — Bill Summary
                    ft.Container(
                        expand=1,
                        content=ft.Column([
                            ft.Text("Bill Summary", size=16, weight=ft.FontWeight.W_600, color="white"),
                            discount,
                            ft.Container(height=8),
                            total_text,
                            net_text,
                            ft.Container(height=16),
                            ft.ElevatedButton(
                                "Generate Bill",
                                bgcolor="#6C63FF",
                                color="white",
                                on_click=save_bill,
                                width=200,
                                height=46,
                            ),
                            ft.Divider(color="#444"),
                            ft.Text("Employee Info", color="#aaaaaa", size=13),
                            employee_id,
                        ], spacing=10),
                        padding=10,
                        bgcolor="#1a1a2e",
                        border_radius=12,
                    ),
                ],
                expand=True,
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )