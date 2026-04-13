
from data.database import users_collection
import hashlib


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(email, password):
    user = users_collection.find_one({"email": email.strip().lower()})
    if not user:
        return None, "Email not found"
    if user["password"] != hash_password(password):
        return None, "Incorrect password"
    return user, None

def register_user(full_name, email, password):
    existing = users_collection.find_one({"email": email.strip().lower()})
    if existing:
        return False, "Email already registered"
    users_collection.insert_one({
        "full_name": full_name,
        "email": email.strip().lower(),
        "password": hash_password(password),
    })
    return True, None