# import flet as ft
# from datetime import datetime
# from pymongo import MongoClient, ReturnDocument
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet


# client = MongoClient("mongodb://localhost:27017/")
# db = client["inventory"]

# products_col = db["products"]
# customers_col = db["customers"]
# sales_col = db["sales"]
# invoices_col = db["invoices"]
# counters_col = db["counters"]


# def get_next_id(name, prefix, base):

#     counter = counters_col.find_one_and_update(
#         {"_id": name},
#         {"$inc": {"seq": 1}},
#         upsert=True,
#         return_document=ReturnDocument.AFTER
#     )


#     if counter["seq"] < base:
#         counters_col.update_one({"_id": name}, {"$set": {"seq": base}})
#         return f"{prefix}{base}"

#     return f"{prefix}{counter['seq']}"



# def update_product_stock(product_id, qty_sold):
#     product = products_col.find_one({"product_id": product_id})

#     if not product:
#         return

#     new_stock = product.get("current_stock", 0) - qty_sold
#     if new_stock < 0:
#         new_stock = 0

#     products_col.update_one(
#         {"product_id": product_id},
#         {
#             "$set": {
#                 "current_stock": new_stock,
#                 "updated_at": datetime.utcnow()
#             }
#         }
#     )



# def main(page: ft.Page):

#     page.title = "Smart Billing System"
#     page.bgcolor = "white"
#     page.window_width = 1400
#     page.window_height = 800

#     cart = []
#     selected_product = {}

#     # ---------------- INPUTS ----------------

#     search = ft.TextField(label="Search Product", expand=True)

#     customer_name = ft.TextField(label="Customer Name")
#     customer_contact = ft.TextField(label="Contact")

#     employee_id = ft.TextField(label="Employee ID")

#     product_name = ft.TextField(label="Product", expand=True, read_only=True)
#     price = ft.TextField(label="Price", width=100)
#     qty = ft.TextField(label="Qty", width=80)

#     discount = ft.TextField(label="Discount %", value="0")

#     # ---------------- TABLE ----------------

#     product_table = ft.DataTable(
#         expand=True,
#         columns=[
#             ft.DataColumn(ft.Text("Name")),
#             ft.DataColumn(ft.Text("Price")),
#             ft.DataColumn(ft.Text("Stock")),
#         ],
#         rows=[]
#     )

#     cart_table = ft.DataTable(
#         expand=True,
#         columns=[
#             ft.DataColumn(ft.Text("Name")),
#             ft.DataColumn(ft.Text("Qty")),
#             ft.DataColumn(ft.Text("Total")),
#         ],
#         rows=[]
#     )

#     total_text = ft.Text("Total: 0")
#     net_text = ft.Text("Net: 0", weight="bold", color="green")

#     # ---------------- LOAD PRODUCTS ----------------

#     def load_products(e=None):
#         product_table.rows.clear()

#         query = search.value.lower() if search.value else ""

#         for p in products_col.find():
#             if query and query not in p.get("name", "").lower():
#                 continue

#             def select(ev, prod=p):
#                 selected_product.clear()
#                 selected_product.update(prod)

#                 product_name.value = prod["name"]
#                 price.value = str(prod["selling_price"])
#                 qty.value = "1"
#                 page.update()

#             product_table.rows.append(
#                 ft.DataRow(cells=[
#                     ft.DataCell(ft.Text(p["name"]), on_tap=select),
#                     ft.DataCell(ft.Text(str(p["selling_price"]))),
#                     ft.DataCell(ft.Text(str(p["current_stock"])))
#                 ])
#             )

#         page.update()



#     def refresh_cart():
#         cart_table.rows.clear()
#         total = 0

#         for item in cart:
#             subtotal = item["price"] * item["qty"]
#             total += subtotal

#             cart_table.rows.append(
#                 ft.DataRow(cells=[
#                     ft.DataCell(ft.Text(item["name"])),
#                     ft.DataCell(ft.Text(str(item["qty"]))),
#                     ft.DataCell(ft.Text(str(subtotal)))
#                 ])
#             )

#         disc = float(discount.value or 0)
#         net = total - (total * disc / 100)

#         total_text.value = f"Total: {total}"
#         net_text.value = f"Net: {net}"

#         page.update()

#     def add_cart(e):
#         if not selected_product:
#             return

#         q = int(qty.value)

#         if q > selected_product["current_stock"]:
#             page.snack_bar = ft.SnackBar(ft.Text("Not enough stock"))
#             page.snack_bar.open = True
#             page.update()
#             return

#         cart.append({
#             "product_id": selected_product["product_id"],
#             "name": selected_product["name"],
#             "price": float(price.value),
#             "qty": q
#         })

#         refresh_cart()

#     def clear_cart(e):
#         cart.clear()
#         refresh_cart()

#     # ---------------- SAVE BILL ----------------

#     def save_bill(e):

#         if not cart:
#             return

#         if not customer_name.value or not employee_id.value:
#             page.snack_bar = ft.SnackBar(ft.Text("Customer & Employee required"))
#             page.snack_bar.open = True
#             page.update()
#             return


#         invoice_id = get_next_id("invoice", "INV", 11000)
#         invoice_number = f"INV{int(datetime.now().timestamp())}"
#         customer_id = get_next_id("customer", "C", 501)


#         customers_col.insert_one({
#             "customer_id": customer_id,
#             "name": customer_name.value,
#             "contact": customer_contact.value,
#             "created_at": datetime.utcnow()
#         })

#         total = sum(i["price"] * i["qty"] for i in cart)
#         disc = float(discount.value or 0)
#         net = total - (total * disc / 100)

#         # ---------------- SALES ----------------
#         for item in cart:

#             sales_col.insert_one({
#                 "sale_id": get_next_id("sale", "s", 35136),
#                 "invoice_id": invoice_id,
#                 "invoice_number": invoice_number,
#                 "product_id": item["product_id"],
#                 "customer_id": customer_id,
#                 "employee_id": employee_id.value,
#                 "qty": item["qty"],
#                 "total": item["price"] * item["qty"],
#                 "date": datetime.utcnow().strftime("%Y-%m-%d")
#             })

#             update_product_stock(item["product_id"], item["qty"])

#         # ---------------- INVOICE ----------------
#         invoices_col.insert_one({
#             "invoice_id": invoice_id,
#             "invoice_number": invoice_number,
#             "customer_id": customer_id,
#             "employee_id": employee_id.value,
#             "items": cart.copy(),
#             "total": total,
#             "discount": disc,
#             "net": net,
#             "created_at": datetime.utcnow().strftime("%Y-%m-%d")
#         })

#         generate_pdf(invoice_number, total, disc, net,
#                      customer_name.value, customer_contact.value, employee_id.value, cart.copy())

#         cart.clear()
#         refresh_cart()

#     # ---------------- PDF ----------------

#     def generate_pdf(invoice, total, disc, net, cname, contact, emp, items):

#         doc = SimpleDocTemplate(f"{invoice}.pdf")
#         styles = getSampleStyleSheet()
#         elements = []

#         elements.append(Paragraph(f"Invoice: {invoice}", styles["Title"]))
#         elements.append(Spacer(1, 10))

#         elements.append(Paragraph(f"Customer: {cname}", styles["Normal"]))
#         elements.append(Paragraph(f"Contact: {contact}", styles["Normal"]))
#         elements.append(Paragraph(f"Employee: {emp}", styles["Normal"]))

#         elements.append(Spacer(1, 10))

#         for item in items:
#             elements.append(Paragraph(
#                 f"{item['name']} {item['qty']} x {item['price']}",
#                 styles["Normal"]
#             ))

#         elements.append(Spacer(1, 10))
#         elements.append(Paragraph(f"Total: {total}", styles["Normal"]))
#         elements.append(Paragraph(f"Discount: {disc}%", styles["Normal"]))
#         elements.append(Paragraph(f"Net: {net}", styles["Normal"]))

#         doc.build(elements)

#     # ---------------- UI ----------------

#     page.add(
#         ft.Row([
#             ft.Container(
#                 expand=2,
#                 content=ft.Column([
#                     ft.Text("Products", size=20, weight="bold"),
#                     ft.Row([search, ft.ElevatedButton("Search", on_click=load_products)]),
#                     product_table
#                 ])
#             ),

#             ft.Container(
#                 expand=2,
#                 content=ft.Column([
#                     ft.Text("Cart & Customer", size=20, weight="bold"),
#                     ft.Row([customer_name, customer_contact]),
#                     cart_table,
#                     ft.Row([product_name, price, qty]),
#                     ft.Row([
#                         ft.ElevatedButton("Add", on_click=add_cart),
#                         ft.ElevatedButton("Clear", on_click=clear_cart)
#                     ])
#                 ])
#             ),

#             ft.Container(
#                 expand=1,
#                 content=ft.Column([
#                     ft.Text("Bill Summary", size=20, weight="bold"),
#                     discount,
#                     total_text,
#                     net_text,
#                     ft.ElevatedButton("Generate Bill", on_click=save_bill),
#                     ft.Divider(),
#                     ft.Text("Employee Info"),
#                     employee_id
#                 ])
#             )
#         ], expand=True)
#     )

#     load_products()

# ft.run(main)