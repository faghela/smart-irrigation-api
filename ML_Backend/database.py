"""
database.py — اتصال MongoDB
MongoDB connection and collection references.
"""
from pymongo import MongoClient
from config import MONGO_URI

client      = None
db          = None
collection  = None   # sensor_data
control_col = None   # pump_control

try:
    client      = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    db          = client['irrigation_db']
    collection  = db['sensor_data']
    control_col = db['pump_control']
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
