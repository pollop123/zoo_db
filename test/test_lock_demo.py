"""
Lock 機制展示腳本
展示多執行緒同時扣庫存時的併發控制

執行方式:
    python test/test_lock_demo.py
"""
import threading
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DB_utils import ZooBackend
from config import *

def get_current_stock(f_id="F001"):
    """查詢目前庫存"""
    backend = ZooBackend()
    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT SUM(quantity_delta_kg) 
                FROM feeding_inventory 
                WHERE f_id = %s
            """, (f_id,))
            result = cur.fetchone()[0]
            return float(result) if result else 0
    finally:
        backend.close()

def feeding_worker(worker_id, a_id, f_id, amount, results):
    """模擬員工餵食操作"""
    print(f"[Worker {worker_id}] 開始餵食 {a_id}，使用 {amount}kg 飼料...")
    
    backend = ZooBackend()
    start_time = time.time()
    
    # 使用 E003 (有 Carnivore 證照，今日值班負責 A002)
    success, msg = backend.add_feeding_record(a_id, f_id, amount, "E003")
    
    elapsed = time.time() - start_time
    backend.close()
    
    results[worker_id] = {
        'success': success,
        'message': msg,
        'time': elapsed
    }
    
    status = "成功" if success else "失敗"
    print(f"[Worker {worker_id}] {status} (耗時 {elapsed:.3f}s): {msg}")

def demo_concurrent_feeding():
    """展示併發餵食的 Lock 機制"""
    print("=" * 60)
    print("併發控制 (Lock) 機制展示")
    print("=" * 60)
    
    # 1. 顯示初始庫存
    initial_stock = get_current_stock("F001")
    print(f"\n[初始狀態] F001 (Beef) 庫存: {initial_stock:.2f} kg")
    
    # 2. 設定測試參數
    num_workers = 5
    feed_amount = 3.0  # 每次餵食 3kg
    total_expected = num_workers * feed_amount
    
    print(f"\n[測試設定]")
    print(f"  - 同時執行 {num_workers} 個餵食操作")
    print(f"  - 每次餵食 {feed_amount} kg")
    print(f"  - 預期總消耗: {total_expected} kg")
    
    # 3. 建立執行緒
    threads = []
    results = {}
    
    print(f"\n[開始測試] 啟動 {num_workers} 個執行緒同時餵食...\n")
    
    for i in range(num_workers):
        t = threading.Thread(
            target=feeding_worker,
            args=(i + 1, "A002", "F001", feed_amount, results)
        )
        threads.append(t)
    
    # 4. 同時啟動所有執行緒
    start_time = time.time()
    for t in threads:
        t.start()
    
    # 5. 等待所有執行緒完成
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    
    # 6. 統計結果
    print("\n" + "=" * 60)
    print("測試結果")
    print("=" * 60)
    
    success_count = sum(1 for r in results.values() if r['success'])
    fail_count = num_workers - success_count
    
    final_stock = get_current_stock("F001")
    actual_consumed = initial_stock - final_stock
    
    print(f"\n[執行統計]")
    print(f"  - 成功: {success_count} 筆")
    print(f"  - 失敗: {fail_count} 筆")
    print(f"  - 總耗時: {total_time:.3f} 秒")
    
    print(f"\n[庫存變化]")
    print(f"  - 初始庫存: {initial_stock:.2f} kg")
    print(f"  - 最終庫存: {final_stock:.2f} kg")
    print(f"  - 實際消耗: {actual_consumed:.2f} kg")
    print(f"  - 預期消耗: {success_count * feed_amount:.2f} kg")
    
    # 7. 驗證 Lock 是否正常運作
    expected_consumed = success_count * feed_amount
    if abs(actual_consumed - expected_consumed) < 0.01:
        print(f"\n[結論] Lock 機制正常運作！庫存扣減正確，無資料競爭問題。")
    else:
        print(f"\n[警告] 庫存扣減異常，可能存在併發問題！")

def demo_lock_timeout():
    """展示 Lock 等待情境"""
    print("\n" + "=" * 60)
    print("Lock 等待展示 (模擬長時間交易)")
    print("=" * 60)
    
    def long_transaction():
        """模擬長時間持有 Lock 的交易"""
        backend = ZooBackend()
        try:
            with backend.get_db_connection() as conn:
                cur = conn.cursor()
                print("[交易 A] 開始長時間交易，鎖定 feeding_inventory...")
                
                # 使用 FOR UPDATE 鎖定資料列
                cur.execute("""
                    SELECT * FROM feeding_inventory 
                    WHERE f_id = 'F001' 
                    ORDER BY stock_entry_id DESC 
                    LIMIT 1 
                    FOR UPDATE
                """)
                
                print("[交易 A] 已取得 Lock，休眠 3 秒模擬長時間操作...")
                time.sleep(3)
                
                conn.commit()
                print("[交易 A] 交易完成，釋放 Lock")
        finally:
            backend.close()
    
    def waiting_transaction():
        """模擬等待 Lock 的交易"""
        time.sleep(0.5)  # 確保交易 A 先執行
        
        backend = ZooBackend()
        try:
            start = time.time()
            print("[交易 B] 嘗試取得 Lock...")
            
            with backend.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT * FROM feeding_inventory 
                    WHERE f_id = 'F001' 
                    ORDER BY stock_entry_id DESC 
                    LIMIT 1 
                    FOR UPDATE
                """)
                
                elapsed = time.time() - start
                print(f"[交易 B] 取得 Lock！等待時間: {elapsed:.2f} 秒")
                conn.commit()
        finally:
            backend.close()
    
    t1 = threading.Thread(target=long_transaction)
    t2 = threading.Thread(target=waiting_transaction)
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    print("\n[結論] 交易 B 必須等待交易 A 釋放 Lock 後才能繼續執行。")

def restore_database():
    """還原資料庫"""
    import subprocess
    
    backup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "zoo.backup")
    
    print("\n[還原] 正在還原資料庫...")
    
    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = PG_PASSWORD
        
        result = subprocess.run(
            ['psql', '-h', PG_HOST, '-p', str(PG_PORT), '-U', PG_USER, '-d', PG_DB, '-f', backup_path],
            capture_output=True,
            text=True,
            env=env
        )
        
        if result.returncode == 0:
            print("[還原] 資料庫已還原至初始狀態")
        else:
            print(f"[還原] 警告: {result.stderr[:100] if result.stderr else '未知錯誤'}")
            
    except FileNotFoundError:
        print("[還原] 錯誤: 找不到 psql，請手動還原:")
        print(f"  psql -U {PG_USER} -d {PG_DB} < zoo.backup")
    except Exception as e:
        print(f"[還原] 錯誤: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Zoo DB Lock 機制展示')
    parser.add_argument('--no-restore', action='store_true', help='展示後不還原資料庫')
    args = parser.parse_args()
    
    print("\n" + "#" * 60)
    print("# Zoo DB - 併發控制 (Lock) 機制展示")
    print("#" * 60)
    
    # 展示 1: 併發餵食
    demo_concurrent_feeding()
    
    # 展示 2: Lock 等待
    demo_lock_timeout()
    
    print("\n" + "#" * 60)
    print("# 展示結束")
    print("#" * 60)
    
    # 自動還原
    if not args.no_restore:
        restore_database()
    else:
        print("\n[提示] 已跳過資料庫還原 (--no-restore)")
