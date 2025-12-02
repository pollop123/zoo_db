import psycopg2
from datetime import datetime, timedelta
from config import *

def setup_shifts():
    print("--- Setting up Shifts & Permissions ---")
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cur = conn.cursor()
        
        # 1. Add a_id column to employee_shift if not exists
        try:
            cur.execute(f"ALTER TABLE {TABLE_EMPLOYEE_SHIFT} ADD COLUMN {COL_ANIMAL_ID} VARCHAR(20);")
            cur.execute(f"ALTER TABLE {TABLE_EMPLOYEE_SHIFT} ADD CONSTRAINT fk_shift_animal FOREIGN KEY ({COL_ANIMAL_ID}) REFERENCES animal(a_id);")
            print("Added 'a_id' column to employee_shift.")
        except psycopg2.errors.DuplicateColumn:
            print("'a_id' column already exists.")
            conn.rollback()
        except Exception as e:
            print(f"Error adding column: {e}")
            conn.rollback()

        # 2. Add 'Daily Care' task (T009)
        try:
            cur.execute(f"INSERT INTO {TABLE_TASK} (t_id, t_name) VALUES ('T009', '日常照護') ON CONFLICT (t_id) DO NOTHING;")
            print("Added Task T009 (日常照護).")
        except Exception as e:
            print(f"Error adding task: {e}")
            conn.rollback()

        # 3. Assign Super Shifts (Today 00:00 - 23:59)
        # E003 -> A001 (胖胖熊/穿山甲)
        # E004 -> A101 (High Risk)
        # E005 -> A002
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')
        today_end = datetime.now().replace(hour=23, minute=59, second=59).strftime('%Y-%m-%d %H:%M:%S')
        
        assignments = [
            ("E003", "A001"),
            ("E004", "A101"),
            ("E005", "A002")
        ]
        
        # Get current Max Shift ID
        cur.execute(f"SELECT MAX(shift_id) FROM {TABLE_EMPLOYEE_SHIFT}")
        max_sid = cur.fetchone()[0]
        if max_sid:
            num_part = int(max_sid[1:])
        else:
            num_part = 0
            
        count = 0
        for e_id, a_id in assignments:
            num_part += 1
            new_sid = f"S{num_part:04d}"
            
            # Check if already assigned today to avoid duplicates
            cur.execute(f"""
                SELECT shift_id FROM {TABLE_EMPLOYEE_SHIFT} 
                WHERE {COL_EMPLOYEE_ID} = %s AND {COL_ANIMAL_ID} = %s AND shift_start = %s
            """, (e_id, a_id, today_start))
            
            if not cur.fetchone():
                query = f"""
                    INSERT INTO {TABLE_EMPLOYEE_SHIFT} (shift_id, {COL_EMPLOYEE_ID}, t_id, shift_start, shift_end, {COL_ANIMAL_ID})
                    VALUES (%s, %s, 'T009', %s, %s, %s)
                """
                cur.execute(query, (new_sid, e_id, today_start, today_end, a_id))
                count += 1
        
        conn.commit()
        print(f"Assigned {count} Super Shifts.")
        print("Super Employees ready: E003->A001, E004->A101, E005->A002")

    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_shifts()
