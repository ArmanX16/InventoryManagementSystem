# Inventory Management System

A desktop inventory management application built with [Flet](https://flet.dev/), featuring AI powered demand forecasting, smart reordering, and real time alerts.

## Requirements

- Python 3.10+
- Flet
- numpy pandas  matplotlib seabon scikit-learn
- pymongo
- xgboost prophet

```bash
pip install flet 
pip install pymongo
pip install pandas
pip install numpy
pip install matplotlib
pip install seaborn
pip install scikit-learn
pip install xgboost prophet
pip install reportlab
```

## Running the App

```bash
cd path/to/inventory_management_app && python main.py
```
## To import database
first open mongodb compass and create a database in mongodb compass 
"inventory" then create collections

- categories
- counters
- customers
- employees
- invoices 
- products
- products_return
- purchase_orders
- sales
- suppliers

after creating database and collection go to each collection and click on import json/csv and select ''inventory database'' folder/directory
and import as it is, do it for each collection. (No need to import data for products_return) 
