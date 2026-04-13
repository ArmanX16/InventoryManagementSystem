import pandas as pd
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["inventory"]

base = "inventory database/"

files = {
    "categories": base + "200_unique_categories.csv",
    "counters": base + "inventory.counters.csv",
    "employees": base + "inventory.employees.csv",
    "invoices": base + "inventory.invoices.csv",
    "products": base + "inventory.products.csv",
    "purchase_orders": base + "inventory.purchase_orders.csv",
    "sales": base + "inventory.sales.csv",
    "suppliers": base + "inventory.suppliers.csv",
}

for collection_name, filepath in files.items():
    try:
        df = pd.read_csv(filepath)
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        records = df.to_dict("records")
        db[collection_name].delete_many({})
        db[collection_name].insert_many(records)
        print(f" {collection_name} — {len(records)} records imported")
    except Exception as ex:
        print(f" {collection_name} failed: {ex}")

# Fix customers separately
try:
    df = pd.read_csv("inventory database/inventory.customers.csv", dtype=str)
    records = df.to_dict("records")
    db["customers"].delete_many({})
    db["customers"].insert_many(records)
    print(f" customers — {len(records)} records imported")
except Exception as ex:
    print(f" customers failed: {ex}")

print("\n All done!")