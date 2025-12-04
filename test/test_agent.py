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
        print("[Test Agent] Initialized. Starting Full Coverage Test (11 Admin + 6 User).")

    def get_backend(self):
        """Create and return a new ZooBackend instance."""
        return ZooBackend()

    def test_user_01_add_feeding(self):
        print("\n[User 1/6] Add Feeding Record...")
        backend = self.get_backend()
        # E003 -> A002 (Lion, requires Carnivore skill - E003 has it and is on shift today)
        success, msg = backend.add_feeding_record("A002", "F001", 5.0, "E003")
        if success:
            print(f"[PASS] Feeding added. Msg: {msg}")
        else:
            print(f"[FAIL] {msg}")
        backend.close()

    def test_user_02_add_body_info(self):
        print("\n[User 2/6] Add Body Info...")
        backend = self.get_backend()
        success, msg = backend.add_animal_state("A002", 205.0, "E003")
        if success:
            print(f"[PASS] Body info added. Msg: {msg}")
        else:
            print(f"[FAIL] {msg}")
        backend.close()

    def test_user_03_view_schedule(self):
        print("\n[User 3/6] View Schedule...")
        backend = self.get_backend()
        data = backend.get_employee_schedule("E003")
        if isinstance(data, list):
            print(f"[PASS] Schedule fetched. Count: {len(data)}")
        else:
            print(f"[FAIL] Failed to fetch schedule.")
        backend.close()

    def test_user_04_view_ref_data(self):
        print("\n[User 4/6] View Reference Data...")
        backend = self.get_backend()
        data = backend.get_reference_data("animal")
        if len(data) > 0:
            print(f"[PASS] Reference data fetched. Count: {len(data)}")
        else:
            print(f"[FAIL] No data found.")
        backend.close()

    def test_user_05_correct_record(self):
        print("\n[User 5/6] Correct Record...")
        backend = self.get_backend()
        # Need a valid record ID. Let's fetch recent one.
        recent = backend.get_recent_records("feeding_records", "A001")
        if recent:
            rec_id = recent[0][0]
            success, msg = backend.correct_record("E003", "feeding_records", rec_id, "feeding_amount_kg", "6.0")
            if success:
                print(f"[PASS] Record corrected. Msg: {msg}")
            else:
                print(f"[FAIL] {msg}")
        else:
            print(f"[SKIP] No recent records to correct.")
        backend.close()

    def test_user_06_view_trends(self):
        print("\n[User 6/6] View Animal Trends...")
        backend = self.get_backend()
        data = backend.get_animal_trends("A001")
        if data:
            print(f"[PASS] Trends fetched. Points: {len(data)}")
        else:
            print(f"[FAIL] No trend data.")
        backend.close()

    def test_admin_01_view_audit(self):
        print("\n[Admin 1/11] View Audit Logs...")
        backend = self.get_backend()
        logs = backend.get_audit_logs()
        if isinstance(logs, list):
            print(f"[PASS] Logs fetched. Count: {len(logs)}")
        else:
            print(f"[FAIL] Failed to fetch logs.")
        backend.close()

    def test_admin_02_batch_scan(self):
        print("\n[Admin 2/11] Batch Anomaly Scan...")
        backend = self.get_backend()
        anomalies = backend.batch_check_anomalies()
        if isinstance(anomalies, list):
            print(f"[PASS] Scan complete. Anomalies found: {len(anomalies)}")
        else:
            print(f"[FAIL] Scan failed.")
        backend.close()

    def test_admin_03_view_inventory(self):
        print("\n[Admin 3/11] View Inventory Report...")
        backend = self.get_backend()
        report = backend.get_inventory_report()
        if len(report) > 0:
            print(f"[PASS] Report generated. Items: {len(report)}")
        else:
            print(f"[FAIL] Empty report.")
        backend.close()

    def test_admin_04_restock(self):
        print("\n[Admin 4/11] Restock Inventory...")
        backend = self.get_backend()
        success, msg = backend.add_inventory_stock("F001", 50.0, "E001")
        if success:
            print(f"[PASS] Restock success. Msg: {msg}")
        else:
            print(f"[FAIL] {msg}")
        backend.close()

    def test_admin_05_assign_task(self):
        print("\n[Admin 5/11] Assign Task...")
        backend = self.get_backend()
        start = (datetime.now() + timedelta(days=2)).replace(hour=10, minute=0).strftime('%Y-%m-%d %H:%M:%S')
        end = (datetime.now() + timedelta(days=2)).replace(hour=12, minute=0).strftime('%Y-%m-%d %H:%M:%S')
        # E003 has Carnivore skill, A005 requires Carnivore
        success, msg = backend.assign_task("E003", "T002", start, end, a_id="A005")
        if success:
            print(f"[PASS] Task assigned. Msg: {msg}")
        else:
            print(f"[FAIL] {msg}")
        backend.close()

    def test_admin_06_correct_record(self):
        print("\n[Admin 6/11] Correct Record (Override)...")
        backend = self.get_backend()
        # Reuse logic from user test
        recent = backend.get_recent_records("feeding_records", "A001")
        if recent:
            rec_id = recent[0][0]
            success, msg = backend.correct_record("E001", "feeding_records", rec_id, "feeding_amount_kg", "7.0")
            if success:
                print(f"[PASS] Admin correction success. Msg: {msg}")
            else:
                print(f"[FAIL] {msg}")
        else:
            print(f"[SKIP] No records.")
        backend.close()

    def test_admin_07_view_high_risk(self):
        print("\n[Admin 7/11] View High Risk Animals...")
        backend = self.get_backend()
        risks = backend.get_high_risk_animals()
        if isinstance(risks, list):
            print(f"[PASS] Risk list fetched. Count: {len(risks)}")
        else:
            print(f"[FAIL] Failed.")
        backend.close()

    def test_admin_08_view_trends(self):
        print("\n[Admin 8/11] View Animal Trends...")
        backend = self.get_backend()
        data = backend.get_animal_trends("A001")
        if data:
            print(f"[PASS] Trends fetched. Points: {len(data)}")
        else:
            print(f"[FAIL] No trend data.")
        backend.close()

    def test_admin_09_view_ref_data(self):
        print("\n[Admin 9/11] View Reference Data...")
        backend = self.get_backend()
        data = backend.get_reference_data("animal")
        if len(data) > 0:
            print(f"[PASS] Reference data fetched. Count: {len(data)}")
        else:
            print(f"[FAIL] No data found.")
        backend.close()

    def test_admin_10_view_careless(self):
        print("\n[Admin 10/11] View Careless Employees...")
        backend = self.get_backend()
        careless = backend.get_careless_employees()
        if isinstance(careless, list):
            print(f"[PASS] Careless list fetched. Count: {len(careless)}")
        else:
            print(f"[FAIL] Failed.")
        backend.close()

    def test_admin_11_manage_skills(self):
        print("\n[Admin 11/11] Manage Skills...")
        backend = self.get_backend()
        success, msg = backend.add_employee_skill("E003", "Bird")
        if success or "duplicate" in msg:
            print(f"[PASS] Skill managed. Msg: {msg}")
        else:
            print(f"[FAIL] {msg}")
        backend.close()

    def run_all(self):
        # User Tests
        self.test_user_01_add_feeding()
        self.test_user_02_add_body_info()
        self.test_user_03_view_schedule()
        self.test_user_04_view_ref_data()
        self.test_user_05_correct_record()
        self.test_user_06_view_trends()
        
        # Admin Tests
        self.test_admin_01_view_audit()
        self.test_admin_02_batch_scan()
        self.test_admin_03_view_inventory()
        self.test_admin_04_restock()
        self.test_admin_05_assign_task()
        self.test_admin_06_correct_record()
        self.test_admin_07_view_high_risk()
        self.test_admin_08_view_trends()
        self.test_admin_09_view_ref_data()
        self.test_admin_10_view_careless()
        self.test_admin_11_manage_skills()
        
        print("\n[Test Agent] All 17 tests completed.")

    def restore_database(self):
        """Restore PostgreSQL database from backup."""
        import subprocess
        
        backup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "zoo.backup")
        
        print("\n[Restore] Restoring database from zoo.backup...")
        
        try:
            # Use psql to restore (zoo.backup is plain SQL format)
            env = os.environ.copy()
            env['PGPASSWORD'] = PG_PASSWORD
            
            result = subprocess.run(
                ['psql', '-h', PG_HOST, '-p', str(PG_PORT), '-U', PG_USER, '-d', PG_DB, '-f', backup_path],
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                print("[Restore] Database restored successfully.")
            else:
                print(f"[Restore] Warning: {result.stderr[:200] if result.stderr else 'Unknown error'}")
                
        except FileNotFoundError:
            print("[Restore] Error: psql not found. Please restore manually:")
            print(f"  psql -U {PG_USER} -d {PG_DB} < zoo.backup")
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
