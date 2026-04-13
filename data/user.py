import hashlib
from database import users_collection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users_collection.insert_one({
    "full_name": "Admin User",
    "email": "admin@company.com",
    "password": hash_password("admin123"),
})

print(" User created successfully!")