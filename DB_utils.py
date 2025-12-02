import psycopg2
import pymongo
from datetime import datetime
import uuid
from decimal import Decimal
from config import *

class ZooBackend:
    def __init__(self):
        # Initialize Database Connections
        self.pg_conn = None
        self.mongo_client = None
        self.mongo_db = None

        # 1. Connect to PostgreSQL
        try:
            self.pg_conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DB,
                user=PG_USER,
                password=PG_PASSWORD
            )
            print("[SUCCESS] Connected to PostgreSQL.")
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

    def login(self, e_id):
        """
        A. 身份驗證與基礎 (Auth)
        1. 查詢 SQL 確認狀態為 active。
        2. [NoSQL] 寫入登入 Log。
        """
        if not self.pg_conn:
            return False, None, None

        try:
            cur = self.pg_conn.cursor()
            # 1. Check SQL
            query = f"SELECT {COL_NAME}, {COL_ROLE} FROM {TABLE_EMPLOYEES} WHERE {COL_EMPLOYEE_ID} = %s AND {COL_STATUS} = 'active'"
            cur.execute(query, (e_id,))
            result = cur.fetchone()

            if result:
                name, role = result
                # 2. [NoSQL] Log login
                log_entry = {
                    "event_type": "LOGIN",
                    "employee_id": e_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "SUCCESS"
                }
                self.mongo_db[COLLECTION_LOGIN_LOGS].insert_one(log_entry)
                return True, name, role
            else:
                # Log failed attempt
                log_entry = {
                    "event_type": "LOGIN",
                    "employee_id": e_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "FAILED"
                }
                self.mongo_db[COLLECTION_LOGIN_LOGS].insert_one(log_entry)
                return False, None, None

        except Exception as e:
            print(f"Login error: {e}")
            if self.pg_conn:
                self.pg_conn.rollback()
            return False, None, None

    def add_feeding(self, a_id, f_id, amount, user_id):
        """
        B. 核心交易 (Transactions) - 飼養員功能
        轉呼叫 add_feeding_record，沿用完整的權限與庫存檢查，並保持舊 API 相容。
        """
        return self.add_feeding_record(a_id, f_id, amount, user_id)

    def add_animal_state(self, a_id, weight, user_id):
        """
        [NEW] 新增動物身體資訊 (User)
        1. INSERT animal_state_record
        """
        if not self.pg_conn:
            return False, "資料庫未連線"

        # 0. Check Permission
        allowed, msg = self.check_shift_permission(user_id, a_id)
        if not allowed:
            return False, msg

        try:
            cur = self.pg_conn.cursor()
            # SQL: record_id(PK), a_id, datetime, weight, state_id, recorded_by
            # Generate ID
            cur.execute(f"SELECT COALESCE(MAX(CAST(record_id AS INTEGER)), 0) + 1 FROM {TABLE_ANIMAL_STATE}")
            new_id = str(cur.fetchone()[0])

            query = f"""
                INSERT INTO {TABLE_ANIMAL_STATE} (record_id, {COL_ANIMAL_ID}, datetime, {COL_WEIGHT}, state_id, recorded_by)
                VALUES (%s, %s, NOW(), %s, 1, %s)
            """
            cur.execute(query, (new_id, a_id, weight, user_id))
            self.pg_conn.commit()
            return True, "身體資訊已更新。"
        except Exception as e:
            self.pg_conn.rollback()
            return False, f"更新失敗: {e}"

    def add_inventory_stock(self, f_id, amount, user_id):
        """
        [NEW] 庫存進貨 (Admin)
        1. INSERT feeding_inventory (positive value)
        """
        if not self.pg_conn:
            return False, "資料庫未連線"

        try:
            cur = self.pg_conn.cursor()
            # SQL: stock_entry_id(PK), f_id, location_id, datetime, quantity_delta_kg, reason, feeding_id
            # Generate ID
            cur.execute(f"SELECT COALESCE(MAX(CAST({COL_STOCK_ID} AS INTEGER)), 0) + 1 FROM {TABLE_INVENTORY}")
            new_inv_id = str(cur.fetchone()[0])
            
            query = f"""
                INSERT INTO {TABLE_INVENTORY} ({COL_STOCK_ID}, {COL_FEED_ID}, {COL_QUANTITY_DELTA}, reason, datetime)
                VALUES (%s, %s, %s, 'purchase', NOW())
            """
            cur.execute(query, (new_inv_id, f_id, float(amount)))
            self.pg_conn.commit()
            return True, "進貨成功。"
        except Exception as e:
            self.pg_conn.rollback()
            return False, f"進貨失敗: {e}"

    def get_employee_schedule(self, e_id):
        """
        [NEW] 查詢員工班表 (User)
        """
        if not self.pg_conn:
            return []

        try:
            cur = self.pg_conn.cursor()
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
            if self.pg_conn:
                self.pg_conn.rollback()
            return []

    def assign_task(self, e_id, t_id, start_time, end_time, a_id=None):
        """
        [NEW] 指派工作/排班 (Admin)
        [Update] 支援指定動物 (a_id) 並檢查技能
        """
        if not self.pg_conn:
            return False, "資料庫未連線"

        try:
            cur = self.pg_conn.cursor()
            
            # 1. Skill Check (Warning)
            if a_id:
                # Get required skill
                cur.execute(f"SELECT required_skill FROM {TABLE_ANIMAL} WHERE {COL_ANIMAL_ID} = %s", (a_id,))
                row = cur.fetchone()
                req_skill = row[0] if row else 'General'
                
                if req_skill != 'General':
                    cur.execute(f"""
                        SELECT skill_id FROM employee_skills 
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
            self.pg_conn.commit()
            return True, "工作指派成功。"
        except Exception as e:
            self.pg_conn.rollback()
            return False, f"指派失敗: {e}"

    def correct_record(self, user_id, table, record_id, col_name, new_val):
        """
        [NEW] 修正紀錄 (Audit Log)
        """
        if not self.pg_conn:
            return False, "資料庫未連線"

        try:
            cur = self.pg_conn.cursor()

            # 1. Select SQL: Get old value
            # Need to know the PK column name. Assuming 'id' or passed in args? 
            # The prompt says "record_id" is the PK. 
            # I'll assume the PK column is named 'id' for simplicity or I need a mapping.
            # For feeding_records, it might be 'feeding_id'.
            
            pk_col = "id" # Default
            creator_col = "recorded_by" # Default

            if table == TABLE_FEEDING:
                pk_col = COL_FEEDING_ID
                creator_col = "fed_by"
            elif table == TABLE_ANIMAL_STATE:
                pk_col = "record_id"
                creator_col = "recorded_by"
            
            # Fetch old value, original creator AND animal_id (if available)
            # We need animal_id to clear alerts if weight is corrected
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
                # This assumes the correction fixes the anomaly
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
            self.pg_conn.commit()
            return True, f"已將 {col_name} 從 {old_val} 修正為 {new_val}"

        except Exception as e:
            self.pg_conn.rollback()
            return False, f"修正失敗: {e}"
            


    def check_weight_anomaly(self, a_id):
        """
        D. 分析與報表 (Analytics) - 園方功能
        1. 呼叫 Window Function SQL 計算變化率。
        2. 若異常 (>5%), [NoSQL] 寫入 health_alerts。
        """
        if not self.pg_conn:
            return False, "資料庫未連線", 0.0

        try:
            cur = self.pg_conn.cursor()

            # 1. Window Function SQL
            # Calculate percentage change from previous weight
            # Assuming table has: animal_id, weight, record_time
            query = f"""
                WITH WeightChanges AS (
                    SELECT 
                        {COL_WEIGHT},
                        LAG({COL_WEIGHT}) OVER (ORDER BY datetime) as prev_weight
                    FROM {TABLE_ANIMAL_STATE}
                    WHERE a_id = %s
                    ORDER BY datetime DESC
                    LIMIT 2
                )
                SELECT {COL_WEIGHT}, prev_weight FROM WeightChanges
            """
            cur.execute(query, (a_id,))
            results = cur.fetchall()

            if len(results) < 2:
                return False, "資料不足，無法分析", 0.0

            current_weight = float(results[0][0])
            prev_weight = float(results[1][0])
            
            if prev_weight == 0:
                 return False, "前次體重為0，無法計算變化率", 0.0

            change_pct = ((current_weight - prev_weight) / prev_weight) * 100

            # 2. Check Anomaly (> 5%)
            if abs(change_pct) > 5:
                alert = {
                    "level": "HIGH",
                    "animal_id": a_id,
                    "message": f"體重驟變 {change_pct:.1f}% (由 {prev_weight}kg 變為 {current_weight}kg)",
                    "created_at": datetime.now().isoformat(),
                    "status": "UNREAD"
                }
                self.mongo_db[COLLECTION_HEALTH_ALERTS].insert_one(alert)
                return True, f"偵測到異常: 體重變化 {change_pct:.1f}%", change_pct
            
            return False, f"體重變化正常: {change_pct:.1f}%", change_pct

        except Exception as e:
            if self.pg_conn:
                self.pg_conn.rollback()
            return False, f"分析失敗: {e}", 0.0

    def batch_check_anomalies(self):
        """
        [NEW] 批量檢查所有動物的體重異常
        """
        if not self.pg_conn:
            return []

        anomalies_found = []
        try:
            cur = self.pg_conn.cursor()
            # Get all live animals
            cur.execute(f"SELECT a_id, a_name FROM animal WHERE life_status = 'In_Zoo'")
            animals = cur.fetchall()
            
            for a_id, a_name in animals:
                is_anomaly, msg, pct = self.check_weight_anomaly(a_id)
                if is_anomaly:
                    anomalies_found.append({
                        "id": a_id,
                        "name": a_name,
                        "msg": msg,
                        "pct": pct
                    })
            
            return anomalies_found
        except Exception as e:
            print(f"Batch check failed: {e}")
            if self.pg_conn:
                self.pg_conn.rollback()
            return []

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
        [NEW] 找出冒失鬼 (被修正次數過多的員工)
        """
        if self.mongo_client is None:
            return []

        try:
            pipeline = [
                {"$match": {"event_type": "DATA_CORRECTION"}},
                {"$group": {"_id": "$original_creator_id", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gte": 5}}}, # 5次以上算冒失鬼
                {"$sort": {"count": -1}}
            ]
            results = list(self.mongo_db[COLLECTION_AUDIT_LOGS].aggregate(pipeline))

            # Enrich with employee names from SQL
            enriched_results = []
            cur = self.pg_conn.cursor()
            for res in results:
                e_id = res['_id']
                if e_id:
                    cur.execute(f"SELECT {COL_NAME} FROM {TABLE_EMPLOYEES} WHERE {COL_EMPLOYEE_ID} = %s", (e_id,))
                    row = cur.fetchone()
                    name = row[0] if row else "Unknown"
                    enriched_results.append({"id": e_id, "name": name, "count": res['count']})
            
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

        if not self.pg_conn:
            return False, "資料庫未連線"
            
        try:
            cur = self.pg_conn.cursor()
            
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
                    SELECT skill_id FROM employee_skills 
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
        if not self.pg_conn:
            return False, "資料庫未連線"
        try:
            cur = self.pg_conn.cursor()
            cur.execute("INSERT INTO employee_skills (e_id, skill_name) VALUES (%s, %s)", (target_e_id, skill_name))
            self.pg_conn.commit()
            return True, f"已授予 {target_e_id} '{skill_name}' 證照。"
        except Exception as e:
            self.pg_conn.rollback()
            return False, f"授證失敗: {e}"

    def add_feeding_record(self, a_id, f_id, amount, user_id):
        """
        [NEW] 新增餵食紀錄 (Transaction)
        - 確認使用者當前班表與技能
        - 驗證庫存並以 Decimal 避免浮點誤差
        - 於同一交易內寫入餵食紀錄與庫存扣減
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

        if not self.pg_conn:
            return False, "資料庫未連線"

        try:
            cur = self.pg_conn.cursor()

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
                self.pg_conn.rollback()
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
            self.pg_conn.commit()
            return True, "餵食紀錄新增成功，庫存已更新"

        except Exception as e:
            self.pg_conn.rollback()
            return False, f"新增餵食紀錄失敗: {e}"

    def check_and_lock_inventory(self, f_id, amount):
        """
        [NEW] 檢查庫存並鎖定相關飼料紀錄以防止競態條件。
        """
        if not self.pg_conn:
            return False, "資料庫未連線"

        try:
            cur = self.pg_conn.cursor()
            
            # [LOCK] Lock the Feed row to prevent Race Condition
            # This ensures only one transaction can modify inventory for this feed at a time
            cur.execute(f"SELECT {COL_FEED_ID} FROM {TABLE_FEEDS} WHERE {COL_FEED_ID} = %s FOR UPDATE", (f_id,))
            
            # 1. Check stock
            # Assuming COL_QUANTITY_DELTA is defined elsewhere, e.g., in constants.py
            # Assuming TABLE_INVENTORY is defined elsewhere, e.g., in constants.py
            cur.execute(f"SELECT SUM(quantity_delta_kg) FROM {TABLE_INVENTORY} WHERE f_id = %s", (f_id,))
            current_stock = cur.fetchone()[0] or 0
            
            if current_stock < amount:
                return False, f"庫存不足! 目前僅剩 {current_stock} kg"
            
            # If stock is sufficient, return True to proceed with the transaction
            return True, f"庫存充足 ({current_stock} kg)"

        except Exception as e:
            if self.pg_conn:
                self.pg_conn.rollback()
            return False, f"庫存檢查失敗: {e}"

    def get_inventory_report(self):
        """
        [NEW] 庫存報表
        """
        if not self.pg_conn:
            return []

        try:
            cur = self.pg_conn.cursor()
            # Aggregate inventory changes by food_id
            query = f"""
                SELECT 
                    f.feed_name, 
                    SUM(i.quantity_delta_kg) as current_stock
                FROM {TABLE_INVENTORY} i
                JOIN feeds f ON i.f_id = f.f_id
                GROUP BY f.feed_name
                ORDER BY current_stock ASC
            """
            cur.execute(query)
            return cur.fetchall()
        except Exception as e:
            print(f"Error fetching inventory report: {e}")
            if self.pg_conn:
                self.pg_conn.rollback()
            return []

    def get_animal_trends(self, a_id):
        """
        [NEW] 動物趨勢 (體重與餵食)
        """
        if not self.pg_conn:
            return {}, {}

        try:
            cur = self.pg_conn.cursor()
            
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
                JOIN feeds f ON r.f_id = f.f_id
                WHERE r.a_id = %s
                ORDER BY feed_date DESC
                LIMIT 5
            """
            cur.execute(feeding_query, (a_id,))
            feedings = cur.fetchall()

            return weights, feedings
        except Exception as e:
            print(f"Error fetching trends: {e}")
            if self.pg_conn:
                self.pg_conn.rollback()
            return {}, {}

    def get_reference_data(self, table_name):
        """
        [NEW] 查詢代碼表 (Reference Lookup)
        """
        if not self.pg_conn:
            return []

        try:
            cur = self.pg_conn.cursor()
            query = ""
            
            if table_name == "animal":
                # Animal table has no name, use species twice or species + sex
                query = f"SELECT a_id, species, sex FROM animal ORDER BY a_id"
            elif table_name == "feeds":
                query = f"SELECT f_id, feed_name, category FROM feeds ORDER BY f_id"
            elif table_name == "task":
                query = f"SELECT t_id, t_name FROM task ORDER BY t_id"
            elif table_name == "employee":
                query = f"SELECT e_id, e_name, role FROM employee ORDER BY e_id"
            else:
                return []

            cur.execute(query)
            return cur.fetchall()
        except Exception as e:
            print(f"Error fetching reference data: {e}")
            if self.pg_conn:
                self.pg_conn.rollback()
            return []

    def get_recent_records(self, table_name, filter_id):
        """
        [NEW] 取得最近的紀錄，輔助修正功能
        """
        if not self.pg_conn:
            return []

        try:
            cur = self.pg_conn.cursor()
            query = ""
            
            if table_name == TABLE_FEEDING:
                # Show ID, Date, Feed Name, Amount
                query = f"""
                    SELECT r.{COL_FEEDING_ID}, r.feed_date, f.feed_name, r.{COL_AMOUNT}
                    FROM {TABLE_FEEDING} r
                    JOIN feeds f ON r.f_id = f.f_id
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
            if self.pg_conn:
                self.pg_conn.rollback()
            return []

    def close(self):
        if self.pg_conn:
            self.pg_conn.close()
        if self.mongo_client:
            self.mongo_client.close()
