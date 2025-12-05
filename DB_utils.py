import psycopg2
import psycopg2.pool
from contextlib import contextmanager
import pymongo
from datetime import datetime
from decimal import Decimal
from config import *

class ZooBackend:
    def __init__(self):
        # Initialize Database Connections
        self.pg_pool = None
        self.mongo_client = None
        self.mongo_db = None

        # 1. Connect to PostgreSQL (Connection Pool)
        try:
            self.pg_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DB,
                user=PG_USER,
                password=PG_PASSWORD
            )
            print("[SUCCESS] Connected to PostgreSQL (Connection Pool Initialized).")
        except Exception as e:
            print(f"[ERROR] PostgreSQL connection error: {e}")

        # 2. Connect to MongoDB
        try:
            self.mongo_client = pymongo.MongoClient(MONGO_URI)
            # Force a connection check
            self.mongo_client.admin.command('ping')
            self.mongo_db = self.mongo_client[MONGO_DB]
            print("[SUCCESS] Connected to MongoDB.")
        except Exception as e:
            print(f"[ERROR] MongoDB connection error: {e}")
            self.mongo_client = None

    @contextmanager
    def get_db_connection(self):
        """
        [NEW] Context manager for getting a connection from the pool.
        Ensures connections are returned to the pool even if exceptions occur.
        Auto-rollbacks if an exception is raised within the block.
        """
        if not self.pg_pool:
            raise Exception("PostgreSQL connection pool is not initialized.")
        
        conn = self.pg_pool.getconn()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pg_pool.putconn(conn)

    def login(self, e_id, password=None):
        """
        A. 身份驗證與基礎 (Auth)
        1. 查詢 SQL 確認狀態為 active。
        2. 驗證密碼 (SHA256)。
        3. [NoSQL] 寫入登入 Log。
        """
        if not self.pg_pool:
            return False, None, None, "資料庫連線池未初始化"

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                # 1. Check SQL (Query without status filter first)
                query = f"SELECT {COL_NAME}, {COL_ROLE}, {COL_STATUS}, password_hash FROM {TABLE_EMPLOYEES} WHERE {COL_EMPLOYEE_ID} = %s"
                cur.execute(query, (e_id,))
                result = cur.fetchone()

                if result:
                    name, role, status, password_hash = result
                    
                    if status != 'active':
                        # Log failed attempt (Inactive)
                        log_entry = {
                            "event_type": "LOGIN",
                            "employee_id": e_id,
                            "timestamp": datetime.now().isoformat(),
                            "status": f"FAILED ({status})"
                        }
                        self.mongo_db[COLLECTION_LOGIN_LOGS].insert_one(log_entry)
                        return False, None, None, f"登入失敗: 帳號狀態異常 ({status})"

                    # 2. 驗證密碼
                    if password:
                        import hashlib
                        input_hash = hashlib.sha256(password.encode()).hexdigest()
                        if input_hash != password_hash:
                            log_entry = {
                                "event_type": "LOGIN",
                                "employee_id": e_id,
                                "timestamp": datetime.now().isoformat(),
                                "status": "FAILED (Wrong Password)"
                            }
                            self.mongo_db[COLLECTION_LOGIN_LOGS].insert_one(log_entry)
                            return False, None, None, "登入失敗: 密碼錯誤"

                    # 3. [NoSQL] Log login (Success)
                    log_entry = {
                        "event_type": "LOGIN",
                        "employee_id": e_id,
                        "timestamp": datetime.now().isoformat(),
                        "status": "SUCCESS"
                    }
                    self.mongo_db[COLLECTION_LOGIN_LOGS].insert_one(log_entry)
                    return True, name, role, "登入成功"
                else:
                    # Log failed attempt (User not found)
                    log_entry = {
                        "event_type": "LOGIN",
                        "employee_id": e_id,
                        "timestamp": datetime.now().isoformat(),
                        "status": "FAILED (Not Found)"
                    }
                    self.mongo_db[COLLECTION_LOGIN_LOGS].insert_one(log_entry)
                    return False, None, None, "登入失敗: 查無此員工 ID"

        except Exception as e:
            print(f"Login error: {e}")
            return False, None, None, f"登入失敗: {e}"

    def get_employee_password(self, e_id):
        """查詢員工密碼（忘記密碼功能，僅供展示）"""
        if not self.pg_pool:
            return None, None, "資料庫連線池未初始化"

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                # 我們存的是 hash，所以回傳預設密碼
                query = f"SELECT {COL_NAME}, password_hash FROM {TABLE_EMPLOYEES} WHERE {COL_EMPLOYEE_ID} = %s"
                cur.execute(query, (e_id,))
                result = cur.fetchone()
                
                if result:
                    name = result[0]
                    # 預設密碼是 zoo123
                    return name, "zoo123", None
                else:
                    return None, None, "查無此員工 ID"
        except Exception as e:
            return None, None, f"查詢失敗: {e}"

    # ===== 員工管理 =====
    
    def change_password(self, e_id, old_password, new_password):
        """修改密碼"""
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"
        
        import hashlib
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                # 驗證舊密碼
                cur.execute(f"SELECT password_hash FROM {TABLE_EMPLOYEES} WHERE {COL_EMPLOYEE_ID} = %s", (e_id,))
                result = cur.fetchone()
                if not result:
                    return False, "查無此員工"
                
                old_hash = hashlib.sha256(old_password.encode()).hexdigest()
                if old_hash != result[0]:
                    return False, "舊密碼錯誤"
                
                # 更新新密碼
                new_hash = hashlib.sha256(new_password.encode()).hexdigest()
                cur.execute(f"UPDATE {TABLE_EMPLOYEES} SET password_hash = %s WHERE {COL_EMPLOYEE_ID} = %s", (new_hash, e_id))
                conn.commit()
                return True, "密碼修改成功"
        except Exception as e:
            return False, f"修改失敗: {e}"

    def get_all_employees(self):
        """取得所有員工列表"""
        if not self.pg_pool:
            return []
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(f"""
                    SELECT {COL_EMPLOYEE_ID}, {COL_NAME}, {COL_ROLE}, {COL_STATUS}
                    FROM {TABLE_EMPLOYEES}
                    ORDER BY {COL_EMPLOYEE_ID}
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching employees: {e}")
            return []

    def add_employee(self, e_id, name, role='User'):
        """新增員工"""
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"
        
        import hashlib
        default_password = hashlib.sha256("zoo123".encode()).hexdigest()
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(f"""
                    INSERT INTO {TABLE_EMPLOYEES} ({COL_EMPLOYEE_ID}, {COL_NAME}, {COL_ROLE}, {COL_STATUS}, password_hash)
                    VALUES (%s, %s, %s, 'active', %s)
                """, (e_id, name, role, default_password))
                conn.commit()
                return True, f"已新增員工 {name} ({e_id})，預設密碼: zoo123"
        except psycopg2.errors.UniqueViolation:
            return False, f"員工 ID {e_id} 已存在"
        except Exception as e:
            return False, f"新增失敗: {e}"

    def update_employee_status(self, e_id, status):
        """更新員工狀態 (active/inactive)"""
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"
        
        if status not in ['active', 'inactive']:
            return False, "狀態必須是 active 或 inactive"
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(f"UPDATE {TABLE_EMPLOYEES} SET {COL_STATUS} = %s WHERE {COL_EMPLOYEE_ID} = %s", (status, e_id))
                if cur.rowcount == 0:
                    return False, "查無此員工"
                conn.commit()
                return True, f"已將員工狀態更新為 {status}"
        except Exception as e:
            return False, f"更新失敗: {e}"

    def update_employee_role(self, e_id, role):
        """更新員工角色"""
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"
        
        if role not in ['Admin', 'User']:
            return False, "角色必須是 Admin 或 User"
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(f"UPDATE {TABLE_EMPLOYEES} SET {COL_ROLE} = %s WHERE {COL_EMPLOYEE_ID} = %s", (role, e_id))
                if cur.rowcount == 0:
                    return False, "查無此員工"
                conn.commit()
                return True, f"已將員工角色更新為 {role}"
        except Exception as e:
            return False, f"更新失敗: {e}"



    def add_animal_state(self, a_id, weight, user_id, state_id=1):
        """
        [NEW] 新增動物身體資訊 (User)
        1. INSERT animal_state_record
        """
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"

        # 0. Validate weight
        try:
            weight_val = float(weight)
        except (TypeError, ValueError):
            return False, "體重格式錯誤"
        
        if weight_val <= 0:
            return False, "體重必須為正數"

        # 0.1 Check Permission
        allowed, msg = self.check_shift_permission(user_id, a_id)
        if not allowed:
            return False, msg

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                
                # 0.5 Get animal info for display
                cur.execute(f"SELECT a_name, species FROM {TABLE_ANIMAL} WHERE a_id = %s", (a_id,))
                animal_info = cur.fetchone()
                animal_name = animal_info[0] if animal_info else a_id
                animal_species = animal_info[1] if animal_info else "未知"
                
                # 1. Generate ID
                cur.execute(f"SELECT COALESCE(MAX(CAST(record_id AS INTEGER)), 0) + 1 FROM {TABLE_ANIMAL_STATE}")
                new_id = str(cur.fetchone()[0])

                # 2. Insert SQL
                query = f"""
                    INSERT INTO {TABLE_ANIMAL_STATE} (record_id, a_id, {COL_WEIGHT}, datetime, recorded_by, state_id)
                    VALUES (%s, %s, %s, NOW(), %s, %s)
                """
                cur.execute(query, (new_id, a_id, weight, user_id, state_id))
                conn.commit()

                # 3. Check Anomaly (NoSQL)
                self.check_weight_anomaly(a_id)
                
                return True, f"已記錄 {animal_name} ({animal_species}) 體重 {weight}kg"
        except Exception as e:
            return False, f"回報失敗: {e}"

    def add_inventory_stock(self, f_id, amount, user_id):
        """
        [NEW] 庫存進貨 (Admin)
        1. INSERT feeding_inventory (positive value)
        """
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"

        # Validate amount
        try:
            amount_val = float(amount)
        except (TypeError, ValueError):
            return False, "進貨數量格式錯誤"
        
        if amount_val <= 0:
            return False, "進貨數量必須為正數"

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                
                # Check if feed exists
                cur.execute(f"SELECT 1 FROM {TABLE_FEEDS} WHERE {COL_FEED_ID} = %s", (f_id,))
                if not cur.fetchone():
                    return False, "飼料不存在"
                
                # Generate ID
                cur.execute(f"SELECT COALESCE(MAX(CAST({COL_STOCK_ID} AS INTEGER)), 0) + 1 FROM {TABLE_INVENTORY}")
                new_sid = str(cur.fetchone()[0])

                query = f"""
                    INSERT INTO {TABLE_INVENTORY} ({COL_STOCK_ID}, f_id, quantity_delta_kg, datetime, reason)
                    VALUES (%s, %s, %s, NOW(), 'purchase')
                """
                cur.execute(query, (new_sid, f_id, amount_val))
                conn.commit()
                return True, "進貨成功，庫存已更新。"
        except Exception as e:
            return False, f"進貨失敗: {e}"

    def get_employee_schedule(self, e_id):
        """
        [NEW] 查詢員工班表 (User)
        """
        if not self.pg_pool:
            return []

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                # Join employee_shift and task to get details
                query = f"""
                    SELECT 
                        s.shift_start, 
                        s.shift_end, 
                        t.t_name,
                        s.a_id
                    FROM {TABLE_EMPLOYEE_SHIFT} s
                    JOIN {TABLE_TASK} t ON s.t_id = t.t_id
                    WHERE s.e_id = %s
                    ORDER BY s.shift_start DESC
                    LIMIT 10
                """
                cur.execute(query, (e_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return []

    def get_my_animals(self, e_id):
        """
        [NEW] 查詢員工目前值班負責的動物
        只回傳今天有排班且時間範圍內的動物
        """
        if not self.pg_pool:
            return []

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                query = f"""
                    SELECT DISTINCT 
                        a.a_id,
                        a.a_name,
                        a.species
                    FROM {TABLE_EMPLOYEE_SHIFT} s
                    JOIN {TABLE_ANIMAL} a ON s.a_id = a.a_id
                    WHERE s.e_id = %s
                      AND s.a_id IS NOT NULL
                      AND s.shift_start <= NOW()
                      AND s.shift_end >= NOW()
                    ORDER BY a.a_id
                """
                cur.execute(query, (e_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching my animals: {e}")
            return []

    def get_all_tasks(self):
        """查詢所有工作類型"""
        if not self.pg_pool:
            return []
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(f"""
                    SELECT t_id, t_name, description
                    FROM {TABLE_TASK}
                    ORDER BY t_id
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching tasks: {e}")
            return []

    def get_all_animals(self):
        """查詢所有動物"""
        if not self.pg_pool:
            return []
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(f"""
                    SELECT a_id, a_name, species, required_skill
                    FROM {TABLE_ANIMAL}
                    ORDER BY a_id
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching animals: {e}")
            return []

    # ===== 飲食管理 =====
    
    def get_animal_diet(self, species):
        """查詢某物種可食用的飼料"""
        if not self.pg_pool:
            return []
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT d.f_id, f.feed_name, f.category
                    FROM animal_diet d
                    JOIN feeds f ON d.f_id = f.f_id
                    WHERE d.species = %s
                    ORDER BY f.category, f.f_id
                """, (species,))
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching animal diet: {e}")
            return []

    def get_all_diet_settings(self):
        """查詢所有物種的飲食設定"""
        if not self.pg_pool:
            return []
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT d.species, d.f_id, f.feed_name, f.category
                    FROM animal_diet d
                    JOIN feeds f ON d.f_id = f.f_id
                    ORDER BY d.species, f.category, f.f_id
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching diet settings: {e}")
            return []

    def add_diet(self, species, f_id):
        """新增某物種可食用的飼料"""
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                # 檢查物種是否存在
                cur.execute("SELECT DISTINCT species FROM animal WHERE species = %s", (species,))
                if not cur.fetchone():
                    return False, f"物種 {species} 不存在"
                
                # 檢查飼料是否存在
                cur.execute("SELECT feed_name FROM feeds WHERE f_id = %s", (f_id,))
                feed = cur.fetchone()
                if not feed:
                    return False, f"飼料 {f_id} 不存在"
                
                cur.execute("INSERT INTO animal_diet (species, f_id) VALUES (%s, %s)", (species, f_id))
                conn.commit()
                return True, f"已新增 {species} 可食用 {feed[0]}"
        except psycopg2.errors.UniqueViolation:
            return False, "此飲食設定已存在"
        except Exception as e:
            return False, f"新增失敗: {e}"

    def remove_diet(self, species, f_id):
        """移除某物種可食用的飼料"""
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM animal_diet WHERE species = %s AND f_id = %s", (species, f_id))
                if cur.rowcount == 0:
                    return False, "找不到此飲食設定"
                conn.commit()
                return True, f"已移除 {species} 的飼料 {f_id}"
        except Exception as e:
            return False, f"移除失敗: {e}"

    def get_all_species(self):
        """取得所有物種列表"""
        if not self.pg_pool:
            return []
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT DISTINCT species FROM animal ORDER BY species")
                return [r[0] for r in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching species: {e}")
            return []

    def get_all_feeds(self):
        """取得所有飼料列表"""
        if not self.pg_pool:
            return []
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT f_id, feed_name, category FROM feeds ORDER BY category, f_id")
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching feeds: {e}")
            return []

    def assign_task(self, e_id, t_id, start_time, end_time, a_id=None):
        """
        [NEW] 指派工作/排班 (Admin)
        [Update] 支援指定動物 (a_id) 並檢查技能
        """
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"

        # Validate time
        from datetime import datetime
        try:
            start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return False, "時間格式錯誤，請使用 YYYY-MM-DD HH:MM:SS"
        
        if end_dt <= start_dt:
            return False, "結束時間必須晚於開始時間"

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                
                # Check if task exists
                cur.execute(f"SELECT 1 FROM {TABLE_TASK} WHERE t_id = %s", (t_id,))
                if not cur.fetchone():
                    return False, "工作項目不存在"
                
                # Check if employee exists
                cur.execute(f"SELECT 1 FROM {TABLE_EMPLOYEES} WHERE {COL_EMPLOYEE_ID} = %s", (e_id,))
                if not cur.fetchone():
                    return False, "員工不存在"
                
                # 1. Skill Check (Warning)
                if a_id:
                    # Get required skill
                    cur.execute(f"SELECT required_skill FROM {TABLE_ANIMAL} WHERE {COL_ANIMAL_ID} = %s", (a_id,))
                    row = cur.fetchone()
                    req_skill = row[0] if row else 'General'
                    
                    if req_skill != 'General':
                        cur.execute(f"""
                            SELECT skill_id FROM {TABLE_EMPLOYEE_SKILLS} 
                            WHERE e_id = %s AND skill_name = %s
                        """, (e_id, req_skill))
                        if not cur.fetchone():
                            # We return False to BLOCK assignment if skill is missing, as per "strict" requirement
                            return False, f"指派失敗: 該員工缺乏 '{req_skill}' 證照，無法負責此動物！"

                # 2. Generate Shift ID (Sxxxx)
                cur.execute(f"SELECT MAX(shift_id) FROM {TABLE_EMPLOYEE_SHIFT}")
                max_sid = cur.fetchone()[0]
                if max_sid:
                    num_part = int(max_sid[1:])
                    new_sid = f"S{num_part + 1:04d}"
                else:
                    new_sid = "S0001"
                
                # 3. Insert
                query = f"""
                    INSERT INTO {TABLE_EMPLOYEE_SHIFT} (shift_id, {COL_EMPLOYEE_ID}, t_id, shift_start, shift_end, {COL_ANIMAL_ID})
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cur.execute(query, (new_sid, e_id, t_id, start_time, end_time, a_id))
                conn.commit()
                return True, "工作指派成功。"
        except Exception as e:
            return False, f"指派失敗: {e}"

    def correct_record(self, user_id, table, record_id, col_name, new_val):
        """
        [NEW] 修正紀錄 (Audit Log)
        """
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"

        # Validate numeric fields
        numeric_fields = [COL_AMOUNT, COL_WEIGHT, 'feeding_amount_kg', 'weight_kg']
        if col_name in numeric_fields:
            try:
                val = float(new_val)
                if val < 0:
                    return False, "數值不能為負數"
            except (TypeError, ValueError):
                return False, "數值格式錯誤"

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()

                # 1. Select SQL: Get old value
                pk_col = "id" # Default
                creator_col = "recorded_by" # Default

                if table == TABLE_FEEDING:
                    pk_col = COL_FEEDING_ID
                    creator_col = "fed_by"
                elif table == TABLE_ANIMAL_STATE:
                    pk_col = "record_id"
                    creator_col = "recorded_by"
                
                # Fetch old value, original creator AND animal_id (if available)
                extra_col = ""
                if table == TABLE_ANIMAL_STATE:
                    extra_col = f", {COL_ANIMAL_ID}"
                
                select_query = f"SELECT {col_name}, {creator_col}{extra_col} FROM {table} WHERE {pk_col} = %s"
                cur.execute(select_query, (record_id,))
                result = cur.fetchone()
                
                if not result:
                    return False, "找不到該筆紀錄"
                
                old_val = result[0]
                original_creator_id = result[1]
                
                # If correcting weight, check if we need to clear alerts
                if table == TABLE_ANIMAL_STATE and col_name == COL_WEIGHT:
                    a_id = result[2]
                    # [Logic] If weight is corrected, remove recent UNREAD alerts for this animal
                    self.mongo_db[COLLECTION_HEALTH_ALERTS].delete_many({
                        "animal_id": a_id,
                        "status": "UNREAD"
                    })

                # 2. Update SQL
                update_query = f"UPDATE {table} SET {col_name} = %s WHERE {pk_col} = %s"
                cur.execute(update_query, (new_val, record_id))

                # 3. Insert NoSQL: Audit Log
                audit_log = {
                    "event_type": "DATA_CORRECTION",
                    "timestamp": datetime.now().isoformat(),
                    "operator_id": user_id,
                    "target_table": table,
                    "record_id": record_id,
                    "change": {
                        "field": col_name,
                        "old_value": float(old_val) if isinstance(old_val, (int, float, Decimal)) else str(old_val),
                        "new_value": float(new_val) if isinstance(new_val, (int, float, Decimal)) else str(new_val)
                    },
                    "original_creator_id": original_creator_id
                }
                self.mongo_db[COLLECTION_AUDIT_LOGS].insert_one(audit_log)

                # 4. Commit
                conn.commit()
                return True, f"已將 {col_name} 從 {old_val} 修正為 {new_val}"

        except Exception as e:
            return False, f"修正失敗: {e}"
            


    def check_weight_anomaly(self, a_id):
        """
        D. 分析與報表 (Analytics) - 園方功能
        改進版：使用近 5 次移動平均來判斷異常
        1. 取得最近 6 筆體重紀錄（當前 + 前 5 次）
        2. 計算前 5 次的移動平均
        3. 當前體重與移動平均比較，偏差 >10% 視為異常
        """
        if not self.pg_pool:
            return False, "資料庫連線池未初始化", 0.0

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()

                # 取得最近 6 筆體重紀錄
                query = f"""
                    WITH RecentWeights AS (
                        SELECT 
                            {COL_WEIGHT},
                            datetime,
                            ROW_NUMBER() OVER (ORDER BY datetime DESC) as rn
                        FROM {TABLE_ANIMAL_STATE}
                        WHERE a_id = %s AND {COL_WEIGHT} IS NOT NULL
                    )
                    SELECT {COL_WEIGHT}, rn FROM RecentWeights WHERE rn <= 6 ORDER BY rn
                """
                cur.execute(query, (a_id,))
                results = cur.fetchall()

                if len(results) < 3:
                    return False, "資料不足（需至少 3 筆），無法分析", 0.0

                current_weight = float(results[0][0])
                # 計算前 N-1 次的移動平均（排除當前）
                prev_weights = [float(r[0]) for r in results[1:]]
                moving_avg = sum(prev_weights) / len(prev_weights)
                
                if moving_avg == 0:
                    return False, "移動平均為0，無法計算變化率", 0.0

                change_pct = ((current_weight - moving_avg) / moving_avg) * 100

                # 偏差 >10% 視為異常（比單次比較更嚴謹）
                if abs(change_pct) > 10:
                    alert = {
                        "level": "HIGH",
                        "animal_id": a_id,
                        "message": f"體重異常 {change_pct:.1f}% (近期平均 {moving_avg:.1f}kg, 當前 {current_weight:.1f}kg)",
                        "created_at": datetime.now().isoformat(),
                        "status": "UNREAD"
                    }
                    self.mongo_db[COLLECTION_HEALTH_ALERTS].insert_one(alert)
                    return True, f"偵測到異常: 體重偏離近期平均 {change_pct:.1f}%", change_pct
                
                return False, f"體重正常: 偏離近期平均 {change_pct:.1f}%", change_pct

        except Exception as e:
            return False, f"分析失敗: {e}", 0.0

    def check_feeding_anomaly(self, a_id):
        """
        檢查動物食量異常
        改進版：使用近 7 天平均而非全歷史平均
        1. 計算近 7 天的平均食量
        2. 當前食量與近期平均比較，偏差 >40% 視為異常
        """
        if not self.pg_pool:
            return False, "資料庫連線池未初始化", 0.0

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()

                # 使用 Window Function 計算近 7 天平均（排除當天）
                query = f"""
                    WITH RecentFeedings AS (
                        SELECT 
                            {COL_AMOUNT},
                            feed_date,
                            ROW_NUMBER() OVER (ORDER BY feed_date DESC) as rn
                        FROM {TABLE_FEEDING}
                        WHERE a_id = %s AND {COL_AMOUNT} IS NOT NULL
                    ),
                    Stats AS (
                        SELECT 
                            {COL_AMOUNT},
                            rn,
                            AVG({COL_AMOUNT}) OVER (
                                ORDER BY rn 
                                ROWS BETWEEN 1 FOLLOWING AND 7 FOLLOWING
                            ) as recent_avg
                        FROM RecentFeedings
                    )
                    SELECT {COL_AMOUNT}, recent_avg FROM Stats WHERE rn = 1
                """
                cur.execute(query, (a_id,))
                result = cur.fetchone()

                if not result or result[1] is None:
                    return False, "食量資料不足（需至少 2 筆），無法分析", 0.0

                latest_amount = float(result[0])
                recent_avg = float(result[1])
                
                if recent_avg == 0:
                    return False, "近期平均食量為0，無法計算變化率", 0.0

                change_pct = ((latest_amount - recent_avg) / recent_avg) * 100

                # 食量偏離近期平均 >40% 視為異常
                if abs(change_pct) > 40:
                    alert = {
                        "level": "MEDIUM",
                        "animal_id": a_id,
                        "message": f"食量異常 {change_pct:.1f}% (近期平均 {recent_avg:.1f}kg, 當前 {latest_amount:.1f}kg)",
                        "created_at": datetime.now().isoformat(),
                        "status": "UNREAD"
                    }
                    self.mongo_db[COLLECTION_HEALTH_ALERTS].insert_one(alert)
                    return True, f"偵測到異常: 食量偏離近期平均 {change_pct:.1f}%", change_pct
                
                return False, f"食量正常: 偏離近期平均 {change_pct:.1f}%", change_pct

        except Exception as e:
            return False, f"分析失敗: {e}", 0.0

    def batch_check_anomalies(self):
        """
        批量檢查所有動物的體重和食量異常
        """
        if not self.pg_pool:
            return []

        anomalies_found = []
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                # Get all live animals
                cur.execute(f"SELECT a_id, a_name FROM animal WHERE life_status = 'In_Zoo'")
                animals = cur.fetchall()
            
            # Connection is returned here.
            # Now iterate and check both weight and feeding anomalies.
            for a_id, a_name in animals:
                # 檢查體重異常
                is_weight_anomaly, weight_msg, weight_pct = self.check_weight_anomaly(a_id)
                if is_weight_anomaly:
                    anomalies_found.append({
                        "id": a_id,
                        "name": a_name,
                        "type": "體重",
                        "msg": weight_msg,
                        "pct": weight_pct
                    })
                
                # 檢查食量異常
                is_feeding_anomaly, feeding_msg, feeding_pct = self.check_feeding_anomaly(a_id)
                if is_feeding_anomaly:
                    anomalies_found.append({
                        "id": a_id,
                        "name": a_name,
                        "type": "食量",
                        "msg": feeding_msg,
                        "pct": feeding_pct
                    })
            
            return anomalies_found
        except Exception as e:
            print(f"Batch check failed: {e}")
            return []

    def log_input_warning(self, user_id, animal_id, warning_type, input_value, expected_value, confirmed):
        """
        [NEW] 記錄輸入警告事件到 MongoDB
        - confirmed=True (忽略警告繼續儲存) → 記錄到 health_alerts (可能是真實健康問題)
        - confirmed=False (取消輸入) → 記錄到 audit_logs (冒失鬼統計用)
        """
        if self.mongo_client is None:
            return False
        
        try:
            log_entry = {
                "event_type": "INPUT_WARNING",
                "employee_id": user_id,
                "animal_id": animal_id,
                "warning_type": warning_type,  # "WEIGHT" or "FEEDING"
                "input_value": float(input_value),
                "expected_value": float(expected_value),
                "confirmed": confirmed,
                "timestamp": datetime.now()
            }
            
            if confirmed:
                # 忽略警告 → 可能是真實健康問題，記錄到 health_alerts
                health_alert = {
                    "animal_id": animal_id,
                    "alert_type": f"CONFIRMED_{warning_type}_ANOMALY",
                    "description": f"員工 {user_id} 確認異常數值: 輸入 {input_value}, 預期 {expected_value:.2f}",
                    "confirmed_by": user_id,
                    "timestamp": datetime.now()
                }
                self.mongo_db[COLLECTION_HEALTH_ALERTS].insert_one(health_alert)
            else:
                # 取消輸入 → 冒失鬼統計用
                self.mongo_db[COLLECTION_AUDIT_LOGS].insert_one(log_entry)
            
            return True
        except Exception as e:
            print(f"Error logging input warning: {e}")
            return False

    def get_audit_logs(self):
        """
        從 MongoDB 撈出修正紀錄給管理員看。
        """
        if self.mongo_client is None:
            return []
        
        try:
            logs = list(self.mongo_db[COLLECTION_AUDIT_LOGS].find().sort("timestamp", -1).limit(50))
            # Convert ObjectId to string for display if needed, or just return dicts
            for log in logs:
                log['_id'] = str(log['_id'])
            return logs
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []

    def get_high_risk_animals(self):
        """
        [NEW] 找出高風險動物 (異常次數過多)
        """
        if self.mongo_client is None:
            return []

        try:
            pipeline = [
                {"$group": {"_id": "$animal_id", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gte": 3}}}, # 假設3次以上算高風險
                {"$sort": {"count": -1}}
            ]
            results = list(self.mongo_db[COLLECTION_HEALTH_ALERTS].aggregate(pipeline))
            return results
        except Exception as e:
            print(f"Error fetching high risk animals: {e}")
    def get_careless_employees(self):
        """
        [NEW] 找出冒失鬼 (被修正次數 + 輸入警告次數過多的員工)
        """
        if not self.pg_pool:
            return []

        try:
            # 統計被修正次數
            correction_pipeline = [
                {"$match": {"event_type": "DATA_CORRECTION"}},
                {"$group": {"_id": "$original_creator_id", "correction_count": {"$sum": 1}}}
            ]
            correction_results = {r['_id']: r['correction_count'] for r in self.mongo_db[COLLECTION_AUDIT_LOGS].aggregate(correction_pipeline)}
            
            # 統計輸入警告次數 (取消輸入的才算冒失鬼，confirmed=False)
            warning_pipeline = [
                {"$match": {"event_type": "INPUT_WARNING"}},
                {"$group": {"_id": "$employee_id", "warning_count": {"$sum": 1}}}
            ]
            warning_results = {r['_id']: r['warning_count'] for r in self.mongo_db[COLLECTION_AUDIT_LOGS].aggregate(warning_pipeline)}
            
            # 合併統計
            all_employees = set(correction_results.keys()) | set(warning_results.keys())
            combined = []
            for e_id in all_employees:
                if e_id:
                    corrections = correction_results.get(e_id, 0)
                    warnings = warning_results.get(e_id, 0)
                    total = corrections + warnings
                    if total >= 3:  # 3次以上算冒失鬼
                        combined.append({
                            "id": e_id,
                            "corrections": corrections,
                            "warnings": warnings,
                            "total": total
                        })
            
            # 按總數排序
            combined.sort(key=lambda x: x['total'], reverse=True)

            # Enrich with employee names from SQL
            enriched_results = []
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                for res in combined:
                    e_id = res['id']
                    cur.execute(f"SELECT {COL_NAME} FROM {TABLE_EMPLOYEES} WHERE {COL_EMPLOYEE_ID} = %s", (e_id,))
                    row = cur.fetchone()
                    name = row[0] if row else "Unknown"
                    enriched_results.append({
                        "id": e_id, 
                        "name": name, 
                        "corrections": res['corrections'],
                        "warnings": res['warnings'],
                        "total": res['total']
                    })
            
            return enriched_results
        except Exception as e:
            print(f"Error fetching careless employees: {e}")
            return []

    # Assuming this new function is where the inventory check and lock should be added.
    # This function is not present in the original document, but the instruction implies its existence.
    # The provided snippet seems to be a mix of existing code and new code.
    # I will create a new placeholder function `check_and_lock_inventory` based on the provided snippet's intent.
    def check_shift_permission(self, e_id, a_id):
        """
        [NEW] 檢查權限: 
        1. 是否有排班負責該動物? (Shift Check)
        2. 是否擁有該動物所需的專業證照? (Skill Check)
        """
        # Admin bypass
        if e_id == "E001": 
            return True, "管理員權限"

        if not self.pg_pool:
            return False, "資料庫連線池未初始化"
            
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                
                # 1. Shift Check
                query_shift = f"""
                    SELECT shift_id FROM {TABLE_EMPLOYEE_SHIFT}
                    WHERE {COL_EMPLOYEE_ID} = %s 
                    AND {COL_ANIMAL_ID} = %s
                    AND NOW() BETWEEN shift_start AND shift_end
                """
                cur.execute(query_shift, (e_id, a_id))
                if not cur.fetchone():
                    return False, "無操作權限: 非值班時間或非負責動物"

                # 2. Skill Check
                # Get required skill for animal
                cur.execute(f"SELECT required_skill FROM {TABLE_ANIMAL} WHERE {COL_ANIMAL_ID} = %s", (a_id,))
                row = cur.fetchone()
                req_skill = row[0] if row else 'General'
                
                if req_skill != 'General':
                    cur.execute(f"""
                        SELECT skill_id FROM {TABLE_EMPLOYEE_SKILLS} 
                        WHERE e_id = %s AND skill_name = %s
                    """, (e_id, req_skill))
                    if not cur.fetchone():
                        return False, f"權限不足: 缺乏 '{req_skill}' 專業證照"

                return True, "權限驗證通過"
        except Exception as e:
            return False, f"權限檢查失敗: {e}"

    def add_employee_skill(self, target_e_id, skill_name):
        """
        [NEW] 新增員工證照 (Admin)
        """
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"
        
        # Validate inputs
        if not target_e_id or not skill_name:
            return False, "員工 ID 和證照名稱不能為空"
        
        # Valid skill types
        valid_skills = ['Carnivore', 'Penguin', 'Endangered']
        if skill_name not in valid_skills:
            return False, f"無效的證照類型，有效選項: {', '.join(valid_skills)}"
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                
                # Check if employee exists
                cur.execute(f"SELECT 1 FROM {TABLE_EMPLOYEES} WHERE {COL_EMPLOYEE_ID} = %s", (target_e_id,))
                if not cur.fetchone():
                    return False, "員工不存在"
                
                cur.execute(f"INSERT INTO {TABLE_EMPLOYEE_SKILLS} (e_id, skill_name) VALUES (%s, %s)", (target_e_id, skill_name))
                conn.commit()
                return True, f"已授予 {target_e_id} '{skill_name}' 證照。"
        except Exception as e:
            return False, f"授證失敗: {e}"

    def add_feeding_record(self, a_id, f_id, amount, user_id):
        """
        [NEW] 新增餵食紀錄 (Transaction)
        - 確認使用者當前班表與技能
        - 以 Decimal 正規化餵食數量，避免浮點誤差並拒絕零/負值
        - 於同一交易內鎖定飼料、檢查庫存、寫入餵食紀錄與庫存扣減
        """
        try:
            normalized_amount = Decimal(str(amount))
        except Exception:
            return False, "餵食數量格式錯誤"

        if normalized_amount <= 0:
            return False, "餵食數量需為正值"

        # 0. Check Permission
        allowed, msg = self.check_shift_permission(user_id, a_id)
        if not allowed:
            return False, msg

        if not self.pg_pool:
            return False, "資料庫連線池未初始化"

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                
                # 0.5 Get animal info for display
                cur.execute(f"SELECT a_name, species FROM {TABLE_ANIMAL} WHERE a_id = %s", (a_id,))
                animal_info = cur.fetchone()
                animal_name = animal_info[0] if animal_info else a_id
                animal_species = animal_info[1] if animal_info else "未知"
                
                # 1. Check and Lock Inventory
                # This ensures only one transaction can modify inventory for this feed at a time
                cur.execute(f"SELECT {COL_FEED_ID} FROM {TABLE_FEEDS} WHERE {COL_FEED_ID} = %s FOR UPDATE", (f_id,))
                
                # [CRITICAL FIX] Lock Tables for Safe ID Generation
                # SHARE ROW EXCLUSIVE mode protects against concurrent data changes and serializes table modifications
                cur.execute(f"LOCK TABLE {TABLE_FEEDING}, {TABLE_INVENTORY} IN SHARE ROW EXCLUSIVE MODE")

                cur.execute(f"SELECT SUM(quantity_delta_kg) FROM {TABLE_INVENTORY} WHERE f_id = %s", (f_id,))
                current_stock = cur.fetchone()[0]
                current_stock = Decimal(current_stock) if current_stock is not None else Decimal("0")
                
                if current_stock < normalized_amount:
                    # No need to rollback explicitly, raising exception triggers it in context manager
                    # But here we want to return False gracefully.
                    # If we return, the context manager exits normally (no exception).
                    # So we should rollback manually? 
                    # Wait, if we return, we exit the 'with' block.
                    # The context manager's 'finally' runs. 'putconn' is called.
                    # The transaction is NOT committed (we didn't call commit).
                    # So it is effectively rolled back (or aborted) by the pool/connection reset?
                    # ThreadedConnectionPool doesn't auto-rollback on putconn.
                    # So we MUST rollback if we exit without commit.
                    conn.rollback()
                    return False, f"庫存不足! 目前僅剩 {current_stock} kg"

                # 2. Insert Feeding Record
                # Generate ID safely under lock
                cur.execute(f"SELECT COALESCE(MAX(CAST({COL_FEEDING_ID} AS INTEGER)), 0) + 1 FROM {TABLE_FEEDING}")
                new_fid = str(cur.fetchone()[0])

                insert_feeding_query = f"""
                    INSERT INTO {TABLE_FEEDING} ({COL_FEEDING_ID}, a_id, f_id, {COL_AMOUNT}, feed_date, fed_by)
                    VALUES (%s, %s, %s, %s, NOW(), %s)
                """
                cur.execute(insert_feeding_query, (new_fid, a_id, f_id, normalized_amount, user_id))

                # 3. Update Inventory (deduct amount)
                # Generate ID
                cur.execute(f"SELECT COALESCE(MAX(CAST({COL_STOCK_ID} AS INTEGER)), 0) + 1 FROM {TABLE_INVENTORY}")
                new_sid = str(cur.fetchone()[0])

                insert_inventory_query = f"""
                    INSERT INTO {TABLE_INVENTORY} ({COL_STOCK_ID}, f_id, quantity_delta_kg, datetime, reason, feeding_id)
                    VALUES (%s, %s, %s, NOW(), 'feeding', %s)
                """
                cur.execute(insert_inventory_query, (new_sid, f_id, -normalized_amount, new_fid))

                # 4. Commit Transaction
                conn.commit()
                return True, f"已餵食 {animal_name} ({animal_species})，庫存已更新"

        except Exception as e:
            return False, f"新增餵食紀錄失敗: {e}"

    def check_and_lock_inventory(self, f_id, amount):
        """
        [NEW] 檢查庫存並鎖定相關飼料紀錄以防止競態條件。
        """
        if not self.pg_pool:
            return False, "資料庫連線池未初始化"

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                
                # [LOCK] Lock the Feed row to prevent Race Condition
                # This ensures only one transaction can modify inventory for this feed at a time
                cur.execute(f"SELECT {COL_FEED_ID} FROM {TABLE_FEEDS} WHERE {COL_FEED_ID} = %s FOR UPDATE", (f_id,))
                
                # 1. Check stock
                cur.execute(f"SELECT SUM(quantity_delta_kg) FROM {TABLE_INVENTORY} WHERE f_id = %s", (f_id,))
                current_stock = cur.fetchone()[0] or 0
                
                if current_stock < amount:
                    return False, f"庫存不足! 目前僅剩 {current_stock} kg"
                
                # If stock is sufficient, return True to proceed with the transaction
                return True, f"庫存充足 ({current_stock} kg)"

        except Exception as e:
            return False, f"庫存檢查失敗: {e}"

    def get_inventory_report(self):
        """
        [NEW] 庫存報表
        """
        if not self.pg_pool:
            return []

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                # Aggregate inventory changes by food_id
                query = f"""
                    SELECT 
                        f.feed_name, 
                        SUM(i.quantity_delta_kg) as current_stock
                    FROM {TABLE_INVENTORY} i
                    JOIN {TABLE_FEEDS} f ON i.f_id = f.f_id
                    GROUP BY f.feed_name
                    ORDER BY current_stock ASC
                """
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching inventory report: {e}")
            return []

    def get_animal_trends(self, a_id):
        """
        [NEW] 動物趨勢 (體重與餵食)
        """
        if not self.pg_pool:
            return {}, {}

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                
                # 1. Recent Weights
                weight_query = f"""
                    SELECT datetime, {COL_WEIGHT}
                    FROM {TABLE_ANIMAL_STATE}
                    WHERE a_id = %s
                    ORDER BY datetime DESC
                    LIMIT 5
                """
                cur.execute(weight_query, (a_id,))
                weights = cur.fetchall()

                # 2. Recent Feedings
                feeding_query = f"""
                    SELECT feed_date, f.feed_name, r.{COL_AMOUNT}
                    FROM {TABLE_FEEDING} r
                    JOIN {TABLE_FEEDS} f ON r.f_id = f.f_id
                    WHERE r.a_id = %s
                    ORDER BY feed_date DESC
                    LIMIT 5
                """
                cur.execute(feeding_query, (a_id,))
                feedings = cur.fetchall()

                return weights, feedings
        except Exception as e:
            print(f"Error fetching trends: {e}")
            return {}, {}

    def get_reference_data(self, table_name):
        """
        [NEW] 查詢代碼表 (Reference Lookup)
        """
        if not self.pg_pool:
            return []

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                query = ""
                
                if table_name == "animal":
                    query = f"SELECT a_id, a_name, species FROM {TABLE_ANIMAL} ORDER BY a_id"
                elif table_name == "feeds":
                    query = f"SELECT f_id, feed_name, category FROM {TABLE_FEEDS} ORDER BY f_id"
                elif table_name == "task":
                    query = f"SELECT t_id, t_name FROM {TABLE_TASK} ORDER BY t_id"
                elif table_name == "employee":
                    query = f"SELECT e_id, e_name, role FROM {TABLE_EMPLOYEES} ORDER BY e_id"
                elif table_name == "status_type":
                    query = f"SELECT s_id, s_name, description FROM {TABLE_STATUS_TYPE} ORDER BY s_id"
                else:
                    return []

                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching reference data: {e}")
            return []

    def get_recent_records(self, table_name, filter_id):
        """
        [NEW] 取得最近的紀錄，輔助修正功能
        """
        if not self.pg_pool:
            return []

        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                query = ""
                
                if table_name == TABLE_FEEDING:
                    # Show ID, Date, Feed Name, Amount
                    query = f"""
                        SELECT r.{COL_FEEDING_ID}, r.feed_date, f.feed_name, r.{COL_AMOUNT}
                        FROM {TABLE_FEEDING} r
                        JOIN {TABLE_FEEDS} f ON r.f_id = f.f_id
                        WHERE r.a_id = %s
                        ORDER BY r.feed_date DESC
                        LIMIT 10
                    """
                elif table_name == TABLE_ANIMAL_STATE:
                    # Show ID, Date, Weight
                    query = f"""
                        SELECT record_id, datetime, {COL_WEIGHT}
                        FROM {TABLE_ANIMAL_STATE}
                        WHERE a_id = %s
                        ORDER BY datetime DESC
                        LIMIT 10
                    """
                else:
                    return []

                cur.execute(query, (filter_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching recent records: {e}")
            return []

    def close(self):
        if self.pg_pool:
            self.pg_pool.closeall()
        if self.mongo_client:
            self.mongo_client.close()
