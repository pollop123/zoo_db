import psycopg2
from config import *

def setup_skills():
    print("--- Setting up Employee Skills System ---")
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cur = conn.cursor()
        
        # 1. Drop animal_schedule (Replacement)
        cur.execute("DROP TABLE IF EXISTS animal_schedule CASCADE;")
        print("Dropped table: animal_schedule")

        # 2. Create employee_skills table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS employee_skills (
                skill_id SERIAL PRIMARY KEY,
                e_id VARCHAR(20) NOT NULL,
                skill_name VARCHAR(50) NOT NULL,
                issue_date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (e_id) REFERENCES employee(e_id) ON DELETE CASCADE
            );
        """)
        print("Created table: employee_skills")

        # 3. Add required_skill to animal table
        try:
            cur.execute("ALTER TABLE animal ADD COLUMN required_skill VARCHAR(50) DEFAULT 'General';")
            print("Added 'required_skill' column to animal.")
        except psycopg2.errors.DuplicateColumn:
            print("'required_skill' column already exists.")
            conn.rollback()

        # 4. Configure Data for Demo
        # A001 (Bear), A101 (Lion) -> Require 'Carnivore'
        cur.execute("UPDATE animal SET required_skill = 'Carnivore' WHERE a_id IN ('A001', 'A101');")
        
        # A002 (Pangolin) -> Requires 'Reptile' (Just for fun/demo)
        cur.execute("UPDATE animal SET required_skill = 'Reptile' WHERE a_id = 'A002';")
        
        print("Updated Animals: A001/A101 need 'Carnivore', A002 needs 'Reptile'.")

        # 5. Assign Skills to Super Employees
        # Clear existing skills first to avoid duplicates if re-run
        cur.execute("TRUNCATE TABLE employee_skills RESTART IDENTITY;")
        
        # E001 (Admin), E003 (Super User), E004 (Super User) get 'Carnivore' & 'Reptile'
        # E006 (Rookie) gets NOTHING (for demo failure)
        
        experts = ['E001', 'E003', 'E004']
        for e_id in experts:
            cur.execute("INSERT INTO employee_skills (e_id, skill_name) VALUES (%s, 'Carnivore')", (e_id,))
            cur.execute("INSERT INTO employee_skills (e_id, skill_name) VALUES (%s, 'Reptile')", (e_id,))
            
        conn.commit()
        print(f"Assigned skills to experts: {experts}")
        print("E006 (Rookie) has NO skills.")

    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_skills()
