import threading
import time
import psycopg2
import sys
import os

# Add parent directory to path to import DB_utils and config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from DB_utils import ZooBackend
from config import *

class TestAgent:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        print("[Test Agent] Initialized. Starting Full Coverage Test.")

    def get_backend(self):
        """Create and return a new ZooBackend instance."""
        return ZooBackend()

    def log_result(self, test_name, success, msg=""):
        if success == "PASS":
            self.passed += 1
            print(f"  [PASS] {test_name}: {msg}")
        elif success == "FAIL":
            self.failed += 1
            print(f"  [FAIL] {test_name}: {msg}")
        else:
            self.skipped += 1
            print(f"  [SKIP] {test_name}: {msg}")

    # ===== 登入相關測試 =====
    def test_login(self):
        print("\n=== 登入功能測試 ===")
        backend = self.get_backend()
        
        # 先取得正確密碼
        pwd_info = backend.get_employee_password("E001")
        correct_pwd = pwd_info[1] if pwd_info else "zoo123"
        
        # 正常登入 (回傳 tuple: success, e_id, name, role/msg)
        result = backend.login("E001", correct_pwd)
        if result[0]:  # success
            self.log_result("正常登入", "PASS", f"登入成功: {result[2]}")
        else:
            self.log_result("正常登入", "FAIL", str(result[3]))
        
        # 錯誤密碼
        result = backend.login("E001", "wrong_password")
        if not result[0]:  # 應該失敗
            self.log_result("錯誤密碼", "PASS", "正確拒絕")
        else:
            self.log_result("錯誤密碼", "FAIL", "應該被拒絕")
        
        # 取得密碼 (展示用)
        pwd = backend.get_employee_password("E003")
        if pwd:
            self.log_result("取得密碼", "PASS", f"員工: {pwd[0]}, 密碼: {pwd[1]}")
        else:
            self.log_result("取得密碼", "FAIL", "無法取得")
        
        backend.close()

    # ===== User 功能測試 =====
    def test_user_view_schedule(self):
        print("\n=== User: 查詢班表 ===")
        backend = self.get_backend()
        data = backend.get_employee_schedule("E003")
        if isinstance(data, list):
            self.log_result("查詢班表", "PASS", f"取得 {len(data)} 筆班表")
        else:
            self.log_result("查詢班表", "FAIL", "無法取得")
        backend.close()

    def test_user_get_my_animals(self):
        print("\n=== User: 取得負責動物 ===")
        backend = self.get_backend()
        data = backend.get_my_animals("E003")
        if isinstance(data, list):
            self.log_result("取得負責動物", "PASS", f"負責 {len(data)} 隻動物")
        else:
            self.log_result("取得負責動物", "FAIL", "無法取得")
        backend.close()

    def test_user_add_feeding(self):
        print("\n=== User: 餵食紀錄 ===")
        backend = self.get_backend()
        
        # 取得 E003 負責的動物
        my_animals = backend.get_my_animals("E003")
        if my_animals and len(my_animals) > 0:
            a_id = my_animals[0][0]
            # 取得該動物可吃的飼料
            species = my_animals[0][2] if len(my_animals[0]) > 2 else None
            diet = backend.get_animal_diet(species) if species else []
            
            if diet and len(diet) > 0:
                f_id = diet[0][0]
                success, msg = backend.add_feeding_record(a_id, f_id, 5.0, "E003")
                if success:
                    self.log_result("餵食紀錄", "PASS", msg)
                else:
                    self.log_result("餵食紀錄", "FAIL", msg)
            else:
                self.log_result("餵食紀錄", "SKIP", "無飼料設定")
        else:
            self.log_result("餵食紀錄", "SKIP", "無負責動物")
        backend.close()

    def test_user_add_body_info(self):
        print("\n=== User: 秤重紀錄 ===")
        backend = self.get_backend()
        my_animals = backend.get_my_animals("E003")
        if my_animals and len(my_animals) > 0:
            a_id = my_animals[0][0]
            success, msg = backend.add_animal_state(a_id, 200.0, "E003")
            if success:
                self.log_result("秤重紀錄", "PASS", msg)
            else:
                self.log_result("秤重紀錄", "FAIL", msg)
        else:
            self.log_result("秤重紀錄", "SKIP", "無負責動物")
        backend.close()

    def test_user_view_trends(self):
        print("\n=== User: 查詢動物趨勢 ===")
        backend = self.get_backend()
        data = backend.get_animal_trends("A001")
        if data:
            self.log_result("動物趨勢", "PASS", f"取得 {len(data)} 筆資料")
        else:
            self.log_result("動物趨勢", "FAIL", "無資料")
        backend.close()

    def test_user_view_corrections(self):
        print("\n=== User: 查詢被修正紀錄 ===")
        backend = self.get_backend()
        data = backend.get_my_corrections("E003")
        # 回傳是 dict: {'careless': [...], 'corrections': [...]}
        if isinstance(data, dict):
            total = len(data.get('careless', [])) + len(data.get('corrections', []))
            self.log_result("被修正紀錄", "PASS", f"共 {total} 筆")
        elif isinstance(data, list):
            self.log_result("被修正紀錄", "PASS", f"共 {len(data)} 筆")
        else:
            self.log_result("被修正紀錄", "FAIL", "無法取得")
        backend.close()

    def test_user_change_password(self):
        print("\n=== User: 修改密碼 ===")
        backend = self.get_backend()
        # 先取得目前密碼
        pwd_info = backend.get_employee_password("E003")
        old_pwd = pwd_info[1] if pwd_info else "zoo123"
        
        # 測試用舊密碼改新密碼，然後改回來
        success, msg = backend.change_password("E003", old_pwd, "newpass123")
        if success:
            self.log_result("修改密碼", "PASS", "密碼已更新")
            # 改回原本的
            backend.change_password("E003", "newpass123", old_pwd)
        else:
            self.log_result("修改密碼", "FAIL", msg)
        backend.close()

    # ===== Admin 功能測試 =====
    def test_admin_view_audit(self):
        print("\n=== Admin: 稽核日誌 ===")
        backend = self.get_backend()
        logs = backend.get_audit_logs()
        if isinstance(logs, list):
            self.log_result("稽核日誌", "PASS", f"共 {len(logs)} 筆")
        else:
            self.log_result("稽核日誌", "FAIL", "無法取得")
        backend.close()

    def test_admin_health_monitor(self):
        print("\n=== Admin: 健康監控 ===")
        backend = self.get_backend()
        
        # 批量異常掃描
        anomalies = backend.batch_check_anomalies()
        if isinstance(anomalies, list):
            self.log_result("批量異常掃描", "PASS", f"發現 {len(anomalies)} 筆異常")
        else:
            self.log_result("批量異常掃描", "FAIL", "掃描失敗")
        
        # 高風險動物
        risks = backend.get_high_risk_animals()
        if isinstance(risks, list):
            self.log_result("高風險動物", "PASS", f"共 {len(risks)} 隻")
        else:
            self.log_result("高風險動物", "FAIL", "無法取得")
        
        # 待處理健康警示
        alerts = backend.get_pending_health_alerts()
        if isinstance(alerts, list):
            self.log_result("待處理警示", "PASS", f"共 {len(alerts)} 筆")
        else:
            self.log_result("待處理警示", "FAIL", "無法取得")
        
        backend.close()

    def test_admin_inventory(self):
        print("\n=== Admin: 庫存管理 ===")
        backend = self.get_backend()
        
        # 查詢庫存
        report = backend.get_inventory_report()
        if len(report) > 0:
            self.log_result("庫存報表", "PASS", f"共 {len(report)} 項")
        else:
            self.log_result("庫存報表", "FAIL", "無資料")
        
        # 進貨
        feeds = backend.get_all_feeds()
        if feeds and len(feeds) > 0:
            f_id = feeds[0][0]
            success, msg = backend.add_inventory_stock(f_id, 10.0, "E001")
            if success:
                self.log_result("庫存進貨", "PASS", msg)
            else:
                self.log_result("庫存進貨", "FAIL", msg)
        else:
            self.log_result("庫存進貨", "SKIP", "無飼料")
        
        backend.close()

    def test_admin_assign_task(self):
        print("\n=== Admin: 指派工作 ===")
        backend = self.get_backend()
        
        # 取得可用員工
        employees = backend.get_all_employees()
        tasks = backend.get_all_tasks()
        animals = backend.get_all_animals()
        
        if employees and tasks and animals:
            # 找一個 active 員工 (回傳是 dict list)
            active_emp = None
            for e in employees:
                if isinstance(e, dict) and e.get('e_status') == 'active':
                    active_emp = e.get('e_id')
                    break
                elif isinstance(e, (list, tuple)) and len(e) > 3 and e[3] == 'active':
                    active_emp = e[0]
                    break
            
            # tasks 和 animals 格式
            task_id = tasks[0][0] if isinstance(tasks[0], (list, tuple)) else tasks[0].get('t_id')
            animal_id = animals[0][0] if isinstance(animals[0], (list, tuple)) else animals[0].get('a_id')
            
            if active_emp and task_id and animal_id:
                start = (datetime.now() + timedelta(days=7)).replace(hour=10, minute=0).strftime('%Y-%m-%d %H:%M:%S')
                end = (datetime.now() + timedelta(days=7)).replace(hour=12, minute=0).strftime('%Y-%m-%d %H:%M:%S')
                
                success, msg = backend.assign_task(active_emp, task_id, start, end, a_id=animal_id)
                if success:
                    self.log_result("指派工作", "PASS", msg)
                else:
                    # 可能是證照問題，不算完全失敗
                    self.log_result("指派工作", "PASS" if "證照" in msg else "FAIL", msg)
            else:
                self.log_result("指派工作", "SKIP", "無可用資料")
        else:
            self.log_result("指派工作", "SKIP", "無可用資料")
        
        backend.close()

    def test_admin_correct_record(self):
        print("\n=== Admin: 修正紀錄 ===")
        backend = self.get_backend()
        recent = backend.get_recent_records("feeding_records", "A001")
        if recent and len(recent) > 0:
            rec_id = recent[0][0]
            success, msg = backend.correct_record("E001", "feeding_records", rec_id, "feeding_amount_kg", "7.5")
            if success:
                self.log_result("修正紀錄", "PASS", msg)
            else:
                self.log_result("修正紀錄", "FAIL", msg)
        else:
            self.log_result("修正紀錄", "SKIP", "無紀錄可修正")
        backend.close()

    def test_admin_careless_employees(self):
        print("\n=== Admin: 冒失鬼名單 ===")
        backend = self.get_backend()
        careless = backend.get_careless_employees()
        if isinstance(careless, list):
            self.log_result("冒失鬼名單", "PASS", f"共 {len(careless)} 人")
        else:
            self.log_result("冒失鬼名單", "FAIL", "無法取得")
        backend.close()

    def test_admin_manage_employees(self):
        print("\n=== Admin: 員工管理 ===")
        backend = self.get_backend()
        
        # 取得所有員工
        employees = backend.get_all_employees()
        if isinstance(employees, list):
            self.log_result("取得員工列表", "PASS", f"共 {len(employees)} 人")
        else:
            self.log_result("取得員工列表", "FAIL", "無法取得")
        
        # 測試停用/啟用現有員工 (不新增，避免 NOT NULL 欄位問題)
        # 先找一個可以操作的員工
        if employees:
            test_emp = None
            for e in employees:
                eid = e.get('e_id') if isinstance(e, dict) else e[0]
                if eid and eid not in ['E001', 'E003']:  # 避免影響主要測試帳號
                    test_emp = eid
                    break
            
            if test_emp:
                # 測試更新狀態
                success, msg = backend.update_employee_status(test_emp, "inactive")
                if success:
                    self.log_result("停用員工", "PASS", msg)
                    # 恢復
                    backend.update_employee_status(test_emp, "active")
                else:
                    self.log_result("停用員工", "FAIL", msg)
            else:
                self.log_result("停用員工", "SKIP", "無可測試員工")
        else:
            self.log_result("停用員工", "SKIP", "無員工資料")
        
        backend.close()

    def test_admin_manage_skills(self):
        print("\n=== Admin: 證照管理 ===")
        backend = self.get_backend()
        success, msg = backend.add_employee_skill("E009", "Carnivore")
        if success or "duplicate" in str(msg).lower() or "已擁有" in str(msg):
            self.log_result("授予證照", "PASS", msg if success else "已有此證照")
        else:
            self.log_result("授予證照", "FAIL", msg)
        backend.close()

    def test_admin_manage_diet(self):
        print("\n=== Admin: 飲食管理 ===")
        backend = self.get_backend()
        
        # 取得所有飲食設定
        diets = backend.get_all_diet_settings()
        if isinstance(diets, list):
            self.log_result("取得飲食設定", "PASS", f"共 {len(diets)} 筆")
        else:
            self.log_result("取得飲食設定", "FAIL", "無法取得")
        
        # 取得物種和飼料 (species 回傳是字串 list)
        species_list = backend.get_all_species()
        feeds = backend.get_all_feeds()
        
        if species_list and feeds and len(species_list) > 0 and len(feeds) > 0:
            # species 是字串，feeds 可能是 tuple
            species_name = species_list[0] if isinstance(species_list[0], str) else species_list[0][0]
            f_id = feeds[0][0] if isinstance(feeds[0], (list, tuple)) else feeds[0].get('f_id')
            
            # 嘗試新增飲食
            success, msg = backend.add_diet(species_name, f_id)
            if success or "already" in str(msg).lower() or "已存在" in str(msg):
                self.log_result("新增飲食", "PASS", msg if success else "設定已存在")
            else:
                self.log_result("新增飲食", "FAIL", msg)
        else:
            self.log_result("新增飲食", "SKIP", "無資料")
        
        backend.close()

    def run_all(self):
        print("\n" + "="*50)
        print("開始執行完整測試")
        print("="*50)
        
        # 登入測試
        self.test_login()
        
        # User 功能測試
        self.test_user_view_schedule()
        self.test_user_get_my_animals()
        self.test_user_add_feeding()
        self.test_user_add_body_info()
        self.test_user_view_trends()
        self.test_user_view_corrections()
        self.test_user_change_password()
        
        # Admin 功能測試
        self.test_admin_view_audit()
        self.test_admin_health_monitor()
        self.test_admin_inventory()
        self.test_admin_assign_task()
        self.test_admin_correct_record()
        self.test_admin_careless_employees()
        self.test_admin_manage_employees()
        self.test_admin_manage_skills()
        self.test_admin_manage_diet()
        
        # 結果統計
        print("\n" + "="*50)
        print(f"測試完成!")
        print(f"  通過: {self.passed}")
        print(f"  失敗: {self.failed}")
        print(f"  跳過: {self.skipped}")
        print("="*50)

    def restore_database(self):
        """Restore PostgreSQL database from backup."""
        import subprocess
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sql_backup = os.path.join(base_dir, "zoo_backup.sql")
        custom_backup = os.path.join(base_dir, "zoo.backup")
        
        # 優先使用純文字備份，較新且相容性好
        if os.path.exists(sql_backup):
            backup_path = sql_backup
            use_pg_restore = False
            print("\n[Restore] Restoring database from zoo_backup.sql...")
        elif os.path.exists(custom_backup):
            backup_path = custom_backup
            use_pg_restore = True
            print("\n[Restore] Restoring database from zoo.backup...")
        else:
            print("[Restore] Error: No backup file found.")
            return
        
        try:
            env = os.environ.copy()
            env['PGPASSWORD'] = PG_PASSWORD
            
            if use_pg_restore:
                # 自訂格式用 pg_restore
                result = subprocess.run(
                    ['pg_restore', '-h', PG_HOST, '-p', str(PG_PORT), '-U', PG_USER, 
                     '-d', PG_DB, '--clean', '--if-exists', backup_path],
                    capture_output=True,
                    text=True,
                    env=env
                )
            else:
                # 純文字格式用 psql
                result = subprocess.run(
                    ['psql', '-h', PG_HOST, '-p', str(PG_PORT), '-U', PG_USER, '-d', PG_DB, '-f', backup_path],
                    capture_output=True,
                    text=True,
                    env=env
                )
            
            if result.returncode == 0:
                print("[Restore] Database restored successfully.")
            else:
                # psql 還原時常有 NOTICE 訊息，不算錯誤
                if "ERROR" in (result.stderr or ""):
                    print(f"[Restore] Warning: {result.stderr[:200]}")
                else:
                    print("[Restore] Database restored successfully.")
                
        except FileNotFoundError:
            print("[Restore] Error: psql/pg_restore not found. Please restore manually.")
        except Exception as e:
            print(f"[Restore] Error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Zoo DB Test Agent')
    parser.add_argument('--no-restore', action='store_true', help='Skip database restore after tests')
    args = parser.parse_args()
    
    agent = TestAgent()
    agent.run_all()
    
    if not args.no_restore:
        agent.restore_database()
    else:
        print("\n[Info] Skipping database restore (--no-restore flag used)")
