# data/database.py
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["inventory"]  

# Collections
product_collection = db["products"]
suppliers_collection = db["suppliers"]
categories_collection = db["categories"]
employees_collection = db["employees"]
users_collection = db["users"]