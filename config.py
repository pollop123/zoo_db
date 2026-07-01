import os

# [Config] 資料庫設定
# 預設值保留展示用設定；部署或不同本機環境可用環境變數覆蓋。

# PostgreSQL Configuration
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "zoo_db")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "password")

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "zoo_nosql")

# Table Names (SQL)
TABLE_FEEDING = "feeding_records"       # 餵食紀錄表
TABLE_ANIMAL_STATE = "animal_state_record" # 體重/狀態紀錄表
TABLE_INVENTORY = "feeding_inventory"   # 庫存表
TABLE_EMPLOYEES = "employee"            # 員工表
TABLE_TASK = "task"                     # 工作項目表
TABLE_EMPLOYEE_SHIFT = "employee_shift" # 員工班表
TABLE_FEEDS = "feeds"                   # 飼料表
TABLE_ANIMAL = "animal"                 # 動物表
TABLE_STATUS_TYPE = "status_type"       # 狀態代碼表

TABLE_EMPLOYEE_SKILLS = "employee_skills" # 員工證照表
TABLE_SPECIES = "species"               # 物種表

# Column Names (SQL)
COL_FEEDING_ID = "feeding_id"
COL_AMOUNT = "feeding_amount_kg"
COL_WEIGHT = "weight"
COL_EMPLOYEE_ID = "e_id"
COL_STATUS = "status"
COL_NAME = "e_name"
COL_ROLE = "role" 
COL_FEED_ID = "f_id"
COL_ANIMAL_ID = "a_id"
COL_ANIMAL_NAME = "a_name"
COL_QUANTITY_DELTA = "quantity_delta_kg"
COL_STOCK_ID = "stock_entry_id"

# Collection Names (NoSQL)
COLLECTION_AUDIT_LOGS = "audit_logs"
COLLECTION_HEALTH_ALERTS = "health_alerts"
COLLECTION_LOGIN_LOGS = "login_logs"
COLLECTION_CARELESS_LOGS = "careless_logs"
