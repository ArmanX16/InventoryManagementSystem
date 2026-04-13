from data.database import product_collection

def get_all_products(limit=None):
    try:
         if limit:
           products = list(product_collection.find(
                {}, {"_id": 0}
            ).limit(limit))
         else:
            products = list(product_collection.find({}, {"_id": 0}))
         print(f" Found {len(products)} products")
         return products
    except Exception as e:
        print(f" Error: {e}")
        return []

def add_product(product_data):
    product_collection.insert_one(product_data)

def delete_product(product_id):
    product_collection.delete_one({"product_id": product_id})

def update_product(product_id, updated_data):
    product_collection.update_one(
        {"product_id": product_id},
        {"$set": updated_data}
    )

def search_products(search_text):
    from data.database import product_collection

    search_text = search_text.strip()

    if not search_text:
        return list(product_collection.find({}, {"_id": 0}))

    result = list(
        product_collection.find(
            {
                "$or": [
                    {"name": {"$regex": f"{search_text}", "$options": "i"}},
                    {"category_id": {"$regex": f"{search_text}", "$options": "i"}},
                    {"supplier_id": {"$regex": f"{search_text}", "$options": "i"}},
                ]
            },
            {"_id": 0}
        )
    )
    return result

