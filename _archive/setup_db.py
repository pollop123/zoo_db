import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import pymongo
import random
from datetime import datetime, timedelta
from config import *

# Config - Change these if your local postgres setup is different
PG_HOST = "localhost"
PG_PORT = "5432"
PG_USER = "postgres"
PG_PASSWORD = "password" # <--- Please check this!
DB_NAME = "zoo_db"
SQL_FILE = "zoo_full_init.sql"

def setup_database():
    print("--- Setting up PostgreSQL Database ---")
    
    # 1. Create Database
    try:
        # Connect to default 'postgres' db to create new db
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASSWORD, database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if db exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"Creating database '{DB_NAME}'...")
            cur.execute(f"CREATE DATABASE {DB_NAME}")
        else:
            print(f"Database '{DB_NAME}' already exists.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Failed to connect/create database: {e}")
        print("Please check your PG_USER and PG_PASSWORD in this script.")
        return

    # 2. Import SQL & Patch Schema
    try:
        print(f"Connecting to '{DB_NAME}'...")
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASSWORD, database=DB_NAME
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Read SQL file
        if os.path.exists(SQL_FILE):
            print(f"Running {SQL_FILE}...")
            with open(SQL_FILE, 'r') as f:
                sql_content = f.read()
                cur.execute(sql_content)
            print("Schema and data imported.")
        else:
            print(f"[WARNING] {SQL_FILE} not found. Skipping import.")

        # 3. Add 'role' column if not exists (Patching for Application Requirements)
        # Note: script.py now generates these columns, so this is just a safety check or can be removed.
        # We will leave it as safety check but it shouldn't trigger.
        print("Verifying schema...")
        
        # 4. Set Admin (e.g., e_id=1) - script.py handles this too, but ensuring it here is fine.
        cur.execute("UPDATE employee SET role = 'Admin' WHERE e_id = 1")
        print("Set Employee ID 1 as Admin.")

        cur.close()
        conn.close()
        print("--- Setup Complete ---")

    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")

def inject_demo_nosql_data():
    """
    Inject demo data into MongoDB for features:
    1. Careless Employee (Audit Logs)
    2. High Risk Animal (Health Alerts)
    """
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[MONGO_DB]
        
        # Clear existing
        db[COLLECTION_AUDIT_LOGS].delete_many({})
        db[COLLECTION_HEALTH_ALERTS].delete_many({})
        print("Cleared existing NoSQL data.")
        
        # 1. Careless Employee Demo
        # Target: Employee E010 (Assuming E010 exists in backup)
        careless_id = "E010" 
        print(f"Injecting Careless Employee logs for ID {careless_id}...")
        
        logs = []
        for i in range(6): # 6 corrections
            logs.append({
                "event_type": "DATA_CORRECTION",
                "timestamp": datetime.now().isoformat(),
                "operator_id": "E001", # Admin
                "target_table": "feeding_records",
                "record_id": str(2000 + i),
                "change": {
                    "field": "feeding_amount_kg",
                    "old_value": 8.0,
                    "new_value": 4.0
                },
                "original_creator_id": careless_id
            })
        db[COLLECTION_AUDIT_LOGS].insert_many(logs)
        
        # 1.1 Random Careless Employees
        # Pick 2 random IDs from E011 to E020
        random_careless = ["E011", "E012"]
        print(f"Injecting Random Careless logs for IDs: {random_careless}...")
        
        for e_id in random_careless:
            logs = []
            for i in range(random.randint(6, 10)): # 6-10 corrections
                logs.append({
                    "event_type": "DATA_CORRECTION",
                    "timestamp": datetime.now().isoformat(),
                    "operator_id": "E001",
                    "target_table": "feeding_records",
                    "record_id": str(3000 + random.randint(1,1000)),
                    "change": {
                        "field": "feeding_amount_kg",
                        "old_value": 8.0,
                        "new_value": 4.0
                    },
                    "original_creator_id": e_id
                })
            db[COLLECTION_AUDIT_LOGS].insert_many(logs)

        # 2. High Risk Animal Demo
        # Target: Animal A101
        high_risk_id = "A101"
        print(f"Injecting Health Alerts for ID {high_risk_id}...")
        
        alerts = []
        for i in range(3): # 3 alerts
            alerts.append({
                "event_type": "WEIGHT_ANOMALY",
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
                "animal_id": high_risk_id,
                "pct_change": 15.0,
                "message": "Weight increased by 15.0%"
            })
        db[COLLECTION_HEALTH_ALERTS].insert_many(alerts)
        
        print("NoSQL Demo Data Injected.")
        
    except Exception as e:
        print(f"Error injecting NoSQL data: {e}")

if __name__ == "__main__":
    # setup_postgresql() # SKIP SQL SETUP - Using Restored Backup
    inject_demo_nosql_data()
