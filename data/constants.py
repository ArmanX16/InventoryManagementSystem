import flet as ft

ALL_PRODUCTS = [
    {
        "id": "P001",
        "name": "Laptop",
        "category": "Electronics",
        "stock": 45,
        "price": 1299.99,
        "reorder": 10,
        "supplier": "HP",
    },
    {
        "id": "P002",
        "name": "Wireless Mouse",
        "category": "Electronics",
        "stock": 8,
        "price": 29.99,
        "reorder": 20,
        "supplier": "HP",
    },
    {
        "id": "P003",
        "name": "Chair",
        "category": "Furniture",
        "stock": 0,
        "price": 349.99,
        "reorder": 5,
        "supplier": "XYZ",
    },
    {
        "id": "P004",
        "name": "Desk",
        "category": "Furniture",
        "stock": 12,
        "price": 599.99,
        "reorder": 8,
        "supplier": "XYZ",
    },
    {
        "id": "P005",
        "name": "USB Cable",
        "category": "Electronics",
        "stock": 3,
        "price": 49.99,
        "reorder": 15,
        "supplier": "ABC",
    },
    {
        "id": "P006",
        "name": "Printer",
        "category": "Electronics",
        "stock": 22,
        "price": 449.99,
        "reorder": 10,
        "supplier": "HP",
    },
    {
        "id": "P007",
        "name": "Headphone",
        "category": "Electronics",
        "stock": 31,
        "price": 129.99,
        "reorder": 12,
        "supplier": "XYZ",
    },
    {
        "id": "P008",
        "name": "Desk Lamp LED",
        "category": "Lighting",
        "stock": 6,
        "price": 39.99,
        "reorder": 10,
        "supplier": "XYZ",
    },
]


ALL_CATEGORIES = [
    {"id": "C001", "name": "Electronics", "products": 5, "value": 89430},
    {"id": "C002", "name": "Furniture", "products": 2, "value": 12399},
    {"id": "C003", "name": "Lighting", "products": 1, "value": 2399},
    {"id": "C004", "name": "Office Supplies", "products": 8, "value": 4120},
]

ALL_SUPPLIERS = [
    {
        "id": "S001",
        "name": "TechCorp",
        "contact": "tech@techcorp.com",
        "products": 2,
        "rating": 4.8,
        "status": "Active",
    },
    {
        "id": "S002",
        "name": "GadgetHub",
        "contact": "info@gadgethub.com",
        "products": 2,
        "rating": 4.5,
        "status": "Active",
    },
    {
        "id": "S003",
        "name": "FurniturePlus",
        "contact": "order@furnplus.com",
        "products": 2,
        "rating": 4.2,
        "status": "Active",
    },
    {
        "id": "S004",
        "name": "DisplayMasters",
        "contact": "sales@dispmas.com",
        "products": 1,
        "rating": 4.7,
        "status": "Active",
    },
    {
        "id": "S005",
        "name": "LightCo",
        "contact": "hi@lightco.com",
        "products": 1,
        "rating": 3.9,
        "status": "Inactive",
    },
]

ALL_EMPLOYEES = [
    {
        "id": "E001",
        "name": "ABC",
        "role": "Inventory Manager",
        "dept": "Operations",
        "status": "Active",
        "email": "abc@company.com",
    },
    {
        "id": "E002",
        "name": "DEF",
        "role": "Sales Representative",
        "dept": "Finance",
        "status": "Active",
        "email": "def@company.com",
    },
    {
        "id": "E003",
        "name": "LMN",
        "role": "Sales Representative",
        "dept": "Finance",
        "status": "Active",
        "email": "lmn@company.com",
    },
    {
        "id": "E004",
        "name": "PQR",
        "role": "Sales Representative",
        "dept": "Finance",
        "status": "On Leave",
        "email": "pqr@company.com",
    },
    {
        "id": "E005",
        "name": "XYZ",
        "role": "Human Resources",
        "dept": "HR",
        "status": "Active",
        "email": "xyz@company.com",
    },
]

ALL_PURCHASE_ORDERS = [
    {
        "id": "PO001",
        "supplier": "HP",
        "product": "Laptop",
        "qty": 20,
        "total": 25999.80,
        "status": "Pending",
        "date": "2026-03-01",
    },
    {
        "id": "PO002",
        "supplier": "HP",
        "product": "Wireless Mouse",
        "qty": 50,
        "total": 1499.50,
        "status": "Approved",
        "date": "2026-02-28",
    },
    {
        "id": "PO003",
        "supplier": "XYZ",
        "product": "Chair",
        "qty": 10,
        "total": 3499.90,
        "status": "Delivered",
        "date": "2026-02-25",
    },
    {
        "id": "PO004",
        "supplier": "XYZ",
        "product": "USB Cable",
        "qty": 30,
        "total": 1499.70,
        "status": "Pending",
        "date": "2026-03-02",
    },
    {
        "id": "PO005",
        "supplier": "XYZ",
        "product": "Desk Lamp LED",
        "qty": 15,
        "total": 599.85,
        "status": "Cancelled",
        "date": "2026-02-20",
    },
]

ALL_ALERTS = [
    {
        "type": "danger",
        "title": "Out of Stock",
        "msg": "Chair (P003) is completely out of stock.",
        "time": "2 min ago",
    },
    {
        "type": "warning",
        "title": "Low Stock Warning",
        "msg": "USB Cable has only 3 units left (threshold: 15).",
        "time": "15 min ago",
    },
    {
        "type": "warning",
        "title": "Low Stock Warning",
        "msg": "Wireless Mouse has only 8 units left (threshold: 20).",
        "time": "1 hour ago",
    },
    {
        "type": "warning",
        "title": "Low Stock Warning",
        "msg": "Desk Lamp LED has only 6 units left (threshold: 10).",
        "time": "3 hour ago",
    },
    {
        "type": "info",
        "title": "AI Forecast Update",
        "msg": "Demand forecast recalculated for Q2 2026.",
        "time": "5 hour ago",
    },
    {
        "type": "success",
        "title": "PO Delivered",
        "msg": "Purchase Order PO003 from XYZ delivered.",
        "time": "1 day ago",
    },
]

NAVIGATION_ITEMS = [
    ("dashboard", ft.Icons.DASHBOARD, "Dashboard"),
    ("products", ft.Icons.INVENTORY, "Products"),
    ("categories", ft.Icons.CATEGORY, "Categories"),
    ("sales", ft.Icons.SHOPPING_CART, "Sales"),
    ("suppliers", ft.Icons.LOCAL_SHIPPING, "Suppliers"),
    ("employees", ft.Icons.PEOPLE, "Employees"),
    ("forecast", ft.Icons.TRENDING_UP, "Demand Forecast"),
    ("reorder", ft.Icons.AUTORENEW, "Smart Reorder"),
    ("risk", ft.Icons.WARNING, "Risk & Alerts"),
    ("analytics", ft.Icons.BAR_CHART, "Analytics"),
    ("data_cleaning", ft.Icons.CLEANING_SERVICES, "Data Cleaning"),
    ("purchase_orders", ft.Icons.RECEIPT, "Purchase Orders"),
    ("admin", ft.Icons.ADMIN_PANEL_SETTINGS, "Admin Panel"),
]

ALL_AI_MODELS = [
    {
        "name": "Demand Forecasting LSTM",
        "type": "Time Series",
        "accuracy": 91.4,
        "status": "Active",
        "last_train": "2026-03-01",
    },
    {
        "name": "Reorder Point Optimizer",
        "type": "Regression",
        "accuracy": 88.7,
        "status": "Active",
        "last_train": "2026-02-28",
    },
    {
        "name": "Anomaly Detector",
        "type": "Unsupervised",
        "accuracy": 94.2,
        "status": "Active",
        "last_train": "2026-02-25",
    },
    {
        "name": "Price Sensitivity Model",
        "type": "Classification",
        "accuracy": 83.1,
        "status": "Training",
        "last_train": "2026-03-03",
    },
    {
        "name": "Supplier Risk Scorer",
        "type": "Ensemble",
        "accuracy": 79.5,
        "status": "Inactive",
        "last_train": "2026-02-10",
    },
]

ADMIN_SYSTEM_SETTINGS = [
    ("Company Name", "Inventory Management", ft.Icons.BUSINESS),
    ("Currency", "INR (₹)", ft.Icons.ATTACH_MONEY),
    ("Timezone", "UTC 5:30", ft.Icons.ACCESS_TIME),
    ("Fiscal Year Start", "January", ft.Icons.CALENDAR_TODAY),
    ("Low Stock Threshold", "10 units", ft.Icons.WARNING),
    ("AI Reorder Mode", "Automatic", ft.Icons.AUTORENEW),
]

ADMIN_NOTIFICATION_SETTINGS = [
    ("Low stock email alerts", True),
    ("Daily inventory digest", True),
    ("AI reorder notifications", True),
    ("Supplier delay alerts", False),
    ("Weekly analytics report", True),
]

ADMIN_SECURITY_SETTINGS = [
    ("Two-factor authentication", True),
    ("Session timeout (30 min)", True),
    ("Audit logging", True),
    ("IP whitelist", False),
]
