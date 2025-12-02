import random
from datetime import datetime, timedelta
from faker import Faker
import json

fake = Faker('zh_TW')

# ================= 參數設定 =================
NUM_EMPLOYEES = 20
NUM_ANIMALS = 50
DAYS_HISTORY = 365
ANOMALY_CHANCE = 0.01

# ================= 名稱產生器 =================

CUTE_NAMES = [
    '團團', '圓圓', '寶寶', '皮皮', '妞妞', '多多', '球球', '小乖', '麻糬', '可樂', 
    '布丁', '豆豆', '花花', '旺財', '來福', '斑斑', '毛毛', '胖虎', '小黑', '小白', 
    '娜娜', '露露', '咪咪', '熊大', '兔兔', '阿呆', '阿瓜', '奇奇', '蒂蒂', '糖糖',
    '波波', '吉吉', '樂樂', '安安', '平平', '壯壯', '美美', '大眼', '捲捲', '布朗',
    '黑糖', '米漿', '奶茶', '咖啡', '歐利', '辛巴', '尼莫', '多莉', '跳跳', '乖乖'
]

used_animal_names = set()
used_employee_names = set()

def get_unique_animal_name():
    """保證產生不重複的動物名字"""
    while True:
        if random.random() < 0.6:
            candidate = random.choice(CUTE_NAMES)
        else:
            prefix = random.choice(['小', '阿', '大', '胖', '呆'])
            char = fake.first_name()[0] 
            candidate = f"{prefix}{char}"
            
        if candidate not in used_animal_names:
            used_animal_names.add(candidate)
            return candidate

def get_unique_employee_name():
    """保證產生不重複的員工名字"""
    while True:
        candidate = fake.name()
        if candidate not in used_employee_names:
            used_employee_names.add(candidate)
            return candidate

# ================= 資料定義 =================
SPECIES_DATA = {
    '大貓熊': {'base_weight': 110, 'deviation': 5, 'feed': '竹子'},
    '非洲獅': {'base_weight': 190, 'deviation': 15, 'feed': '生肉'},
    '亞洲象': {'base_weight': 3500, 'deviation': 100, 'feed': '牧草'},
    '國王企鵝': {'base_weight': 14, 'deviation': 2, 'feed': '鮮魚'},
    '長頸鹿': {'base_weight': 1000, 'deviation': 50, 'feed': '樹葉'},
    '馬來貘': {'base_weight': 350, 'deviation': 30, 'feed': '水果'}
}

# Spec: {In_Zoo, Deceased, Transferred, Loaned_Out}
LIFE_STATUS_OPTIONS = ['In_Zoo'] * 40 + ['Loaned_Out'] * 5 + ['Deceased'] * 3 + ['Transferred'] * 2

STATUS_TYPES = [
    (1, '健康', '各項數值正常，精神良好'),
    (2, '受傷', '外傷、骨折或術後恢復中'),
    (3, '懷孕', '妊娠期，需隔離觀察與營養補充'),
    (4, '生病', '食慾不振、感染或發燒')
]

FEEDS = [
    (1, '竹子', 'plant'),
    (2, '生肉', 'meat'),
    (3, '牧草', 'plant'),
    (4, '鮮魚', 'meat'),
    (5, '樹葉', 'plant'),
    (6, '水果', 'plant')
]

TASKS = [
    (1, '日常餵食'),
    (2, '環境清潔'),
    (3, '健康檢查'),
    (4, '設施維修')
]

ANIMAL_LOCATIONS = [
    '亞洲熱帶雨林區', '非洲草原區', '溫帶動物區', '企鵝館', '無尾熊館', '兩棲爬蟲館', '昆蟲館'
]

def generate_full_sql():
    filename = 'zoo_full_init.sql'
    print(f"正在生成 SQL 腳本: {filename} (已開啟重複名稱過濾)...")
    f = open(filename, 'w', encoding='utf-8')
    
    # ================= PART 1: Drop Tables =================
    f.write("-- [Part 1] 清除舊資料表\n")
    tables_to_drop = [
        "feeding_inventory", "feeding_records", "animal_state_record", 
        "employee_shift", "animal_schedule", 
        "animal", "employee", "feeds", "status_type", "task"
    ]
    for table in tables_to_drop:
        f.write(f"DROP TABLE IF EXISTS {table} CASCADE;\n")
    f.write("\n")

    # ================= PART 2: Create Tables =================
    f.write("-- [Part 2] 建立資料表\n")
    
    f.write("""
CREATE TABLE employee (
    e_id BIGINT PRIMARY KEY,
    e_name VARCHAR(80) NOT NULL,
    sex VARCHAR(10) NOT NULL CHECK (sex IN ('M', 'F', 'Unknown')),
    phone VARCHAR(30),
    start_time TIMESTAMP,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'inactive', 'leave')),
    role VARCHAR(20) NOT NULL CHECK (role IN ('Admin', 'User'))
);
CREATE TABLE status_type (
    s_id BIGINT PRIMARY KEY,
    s_name VARCHAR(80) NOT NULL UNIQUE,
    description TEXT
);
CREATE TABLE feeds (
    f_id BIGINT PRIMARY KEY,
    feed_name VARCHAR(80) NOT NULL,
    category VARCHAR(40) CHECK (category IN ('meat', 'plant', 'processed', 'other'))
);
CREATE TABLE task (
    t_id BIGINT PRIMARY KEY,
    t_name VARCHAR(80) NOT NULL
);
CREATE TABLE animal (
    a_id BIGINT PRIMARY KEY,
    a_name VARCHAR(80),
    species VARCHAR(80) NOT NULL,
    sex VARCHAR(10) NOT NULL CHECK (sex IN ('M', 'F', 'Unknown')),
    life_status VARCHAR(20) NOT NULL CHECK (life_status IN ('In_Zoo', 'Deceased', 'Transferred', 'Loaned_Out'))
);
CREATE TABLE animal_state_record (
    record_id BIGINT PRIMARY KEY,
    a_id BIGINT NOT NULL,
    datetime TIMESTAMP NOT NULL,
    weight NUMERIC(7,2),
    state_id BIGINT,
    recorded_by BIGINT,
    FOREIGN KEY (a_id) REFERENCES animal(a_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (state_id) REFERENCES status_type(s_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (recorded_by) REFERENCES employee(e_id) ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE TABLE feeding_records (
    feeding_id BIGINT PRIMARY KEY,
    a_id BIGINT NOT NULL,
    f_id BIGINT NOT NULL,
    feed_date TIMESTAMP NOT NULL,
    feeding_amount_kg NUMERIC(7,2) NOT NULL,
    fed_by BIGINT,
    FOREIGN KEY (a_id) REFERENCES animal(a_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (f_id) REFERENCES feeds(f_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (fed_by) REFERENCES employee(e_id) ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE TABLE feeding_inventory (
    stock_entry_id BIGINT PRIMARY KEY,
    f_id BIGINT NOT NULL,
    location_id BIGINT,
    datetime TIMESTAMP NOT NULL,
    quantity_delta_kg NUMERIC(10,3) NOT NULL,
    reason VARCHAR(30) NOT NULL CHECK (reason IN ('purchase', 'feeding', 'wastage', 'adjustment')),
    feeding_id BIGINT,
    recorded_by BIGINT,
    FOREIGN KEY (f_id) REFERENCES feeds(f_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (feeding_id) REFERENCES feeding_records(feeding_id) ON DELETE CASCADE ON UPDATE SET NULL,
    FOREIGN KEY (recorded_by) REFERENCES employee(e_id) ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE TABLE employee_shift (
    shift_id BIGINT PRIMARY KEY,
    e_id BIGINT NOT NULL,
    t_id BIGINT NOT NULL,
    shift_start TIMESTAMP NOT NULL,
    shift_end TIMESTAMP NOT NULL,
    FOREIGN KEY (e_id) REFERENCES employee(e_id) ON DELETE CASCADE,
    FOREIGN KEY (t_id) REFERENCES task(t_id) ON DELETE CASCADE
);
CREATE TABLE animal_schedule (
    schedule_id BIGINT PRIMARY KEY,
    a_id BIGINT NOT NULL,
    work_start TIMESTAMP NOT NULL,
    work_end TIMESTAMP NOT NULL,
    location VARCHAR(80) NOT NULL,
    FOREIGN KEY (a_id) REFERENCES animal(a_id) ON DELETE CASCADE
);
CREATE INDEX idx_animal_state_lookup ON animal_state_record (a_id, datetime);
CREATE INDEX idx_feeding_lookup ON feeding_records (a_id, feed_date);
\n""")

    # ================= PART 3: Insert Data =================
    f.write("-- [Part 3] 插入模擬資料\n")
    
    # 3.1 基礎資料
    for s in STATUS_TYPES:
        f.write(f"INSERT INTO status_type VALUES ({s[0]}, '{s[1]}', '{s[2]}');\n")
    for feed in FEEDS:
        f.write(f"INSERT INTO feeds VALUES ({feed[0]}, '{feed[1]}', '{feed[2]}');\n")
    for task in TASKS:
        f.write(f"INSERT INTO task VALUES ({task[0]}, '{task[1]}');\n")
        
    # 3.2 員工
    employee_ids = []
    for i in range(1, NUM_EMPLOYEES + 1):
        unique_e_name = get_unique_employee_name()
        # Assign Role: Employee 1 is Admin, others are User
        role = 'Admin' if i == 1 else 'User'
        f.write(f"INSERT INTO employee VALUES ({i}, '{unique_e_name}', '{random.choice(['M','F'])}', '{fake.phone_number()}', '{fake.date_between(start_date='-5y', end_date='today')}', 'active', '{role}');\n")
        employee_ids.append(i)

    # [Demo Data] Employee 100: 陳大雷 (Careless Employee)
    f.write(f"INSERT INTO employee VALUES (100, '陳大雷', 'M', '0912345678', '2023-01-01', 'active', 'User');\n")
    employee_ids.append(100)

    # 3.3 動物
    animal_data = []
    a_id_counter = 1
    for _ in range(NUM_ANIMALS):
        species = random.choice(list(SPECIES_DATA.keys()))
        info = SPECIES_DATA[species]
        life_status = random.choice(LIFE_STATUS_OPTIONS)
        current_weight = info['base_weight'] + random.uniform(-info['deviation'], info['deviation'])
        
        unique_a_name = get_unique_animal_name()
        
        f.write(f"INSERT INTO animal VALUES ({a_id_counter}, '{unique_a_name}', '{species}', '{random.choice(['M','F'])}', '{life_status}');\n")
        # [Demo Data] Random High Risk (~1% chance)
        is_high_risk = False
        if random.random() < 0.02: # 2% chance to be high risk
            is_high_risk = True
            
        animal_data.append({'id': a_id_counter, 'species': species, 'weight': current_weight, 'info': info, 'status': life_status, 'is_high_risk': is_high_risk})
        a_id_counter += 1

    # [Demo Data] Animal 100: 胖胖熊 (Weight Anomaly)
    panda_info = SPECIES_DATA['大貓熊']
    f.write(f"INSERT INTO animal VALUES (100, '胖胖熊', '大貓熊', 'M', 'In_Zoo');\n")
    animal_data.append({'id': 100, 'species': '大貓熊', 'weight': 120.0, 'info': panda_info, 'status': 'In_Zoo'})

    # [Demo Data] Animal 101: 玻璃獅 (High Risk)
    lion_info = SPECIES_DATA['非洲獅']
    f.write(f"INSERT INTO animal VALUES (101, '玻璃獅', '非洲獅', 'F', 'In_Zoo');\n")
    animal_data.append({'id': 101, 'species': '非洲獅', 'weight': 180.0, 'info': lion_info, 'status': 'In_Zoo'})

    # 3.4 歷史紀錄
    record_id_counter = 1
    feeding_id_counter = 1
    stock_entry_id_counter = 1
    shift_id_counter = 1
    schedule_id_counter = 1
    
    start_date = datetime.now() - timedelta(days=DAYS_HISTORY)
    
    print(f"正在生成約 {DAYS_HISTORY} 天的歷史紀錄，請稍候...")
    
    # 初始庫存 (每個飼料先進貨 1000kg)
    for feed in FEEDS:
        f_id = feed[0]
        # Initial stock recorded by Admin (ID 1)
        f.write(f"INSERT INTO feeding_inventory VALUES ({stock_entry_id_counter}, {f_id}, {random.randint(1, 5)}, '{start_date}', 5000, 'purchase', NULL, 1);\n")
        stock_entry_id_counter += 1

    for day in range(DAYS_HISTORY):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # --- 1. 員工排班 (Employee Shift) ---
        # 每天安排約 70% 員工上班
        working_employees = random.sample(employee_ids, k=int(len(employee_ids) * 0.7))
        for e_id in working_employees:
            # 早班 08:00-16:00 或 晚班 13:00-21:00
            if random.random() < 0.6:
                s_start = current_date.replace(hour=8, minute=0, second=0)
                s_end = current_date.replace(hour=16, minute=0, second=0)
            else:
                s_start = current_date.replace(hour=13, minute=0, second=0)
                s_end = current_date.replace(hour=21, minute=0, second=0)
            
            t_id = random.choice([t[0] for t in TASKS])
            f.write(f"INSERT INTO employee_shift VALUES ({shift_id_counter}, {e_id}, {t_id}, '{s_start}', '{s_end}');\n")
            shift_id_counter += 1

        # --- 2. 動物行程 (Animal Schedule) ---
        # 每天部分動物有展示行程
        display_animals = random.sample(animal_data, k=int(len(animal_data) * 0.5))
        for animal in display_animals:
            if animal['status'] == 'In_Zoo':
                loc = random.choice(ANIMAL_LOCATIONS)
                # 展示時間 09:00 - 17:00
                w_start = current_date.replace(hour=9, minute=0, second=0)
                w_end = current_date.replace(hour=17, minute=0, second=0)
                f.write(f"INSERT INTO animal_schedule VALUES ({schedule_id_counter}, {animal['id']}, '{w_start}', '{w_end}', '{loc}');\n")
                schedule_id_counter += 1

        # --- 3. 餵食與庫存 (Feeding & Inventory) ---
        for animal in animal_data:
            if animal['status'] != 'In_Zoo': continue
            
            fed_by = random.choice(working_employees) # 由當天上班員工餵食
            f_id = next(item[0] for item in FEEDS if item[1] == animal['info']['feed'])
            
            # 餵食量
            amount = round(random.uniform(1.0, 5.0), 2)
            if animal['species'] == '亞洲象': amount = round(random.uniform(30.0, 50.0), 2)
            
            # 餵食時間 (隨機在 09:00-17:00 之間)
            feed_time = current_date.replace(hour=random.randint(9, 16), minute=random.randint(0, 59))
            
            f.write(f"INSERT INTO feeding_records VALUES ({feeding_id_counter}, {animal['id']}, {f_id}, '{feed_time}', {amount}, {fed_by});\n")
            f.write(f"INSERT INTO feeding_inventory VALUES ({stock_entry_id_counter}, {f_id}, {random.randint(1,5)}, '{feed_time}', -{amount}, 'feeding', {feeding_id_counter}, {fed_by});\n")
            
            feeding_id_counter += 1
            stock_entry_id_counter += 1
            
        # --- 4. 定期進貨 (每 7 天進貨一次) ---
        if day % 7 == 0:
            for feed in FEEDS:
                f_id = feed[0]
                # 進貨量 2000-3000kg (Increased to cover consumption), recorded by Admin (1)
                qty = random.randint(2000, 3000)
                f.write(f"INSERT INTO feeding_inventory VALUES ({stock_entry_id_counter}, {f_id}, {random.randint(1,5)}, '{date_str}', {qty}, 'purchase', NULL, 1);\n")
                stock_entry_id_counter += 1

        # --- 5. 動物狀態紀錄 (每 7 天一次) ---
        if day % 7 == 0:
            for animal in animal_data:
                if animal['status'] != 'In_Zoo': continue

                fluctuation = animal['weight'] * random.uniform(-0.02, 0.02)
                state_id = 1 # Default healthy
                if random.random() < ANOMALY_CHANCE:
                    fluctuation = - (animal['weight'] * 0.15)
                    state_id = 4 # 生病
                
                # [Demo Data] Force Anomaly for 胖胖熊 (ID 100) on the last day
                if animal['id'] == 100 and day >= DAYS_HISTORY - 7:
                    fluctuation = animal['weight'] * 0.15 # +15% weight gain
                    state_id = 1

                # [Demo Data] Random High Risk Animals (Multiple anomalies)
                if animal.get('is_high_risk', False) and random.random() < 0.1: # Frequent anomalies
                     fluctuation = animal['weight'] * random.choice([0.15, -0.15])
                     state_id = 4

                # [Demo Data] Random Weight Anomaly (~2% chance for any animal on last record)
                if day == DAYS_HISTORY - 1 and random.random() < 0.02:
                    fluctuation = animal['weight'] * random.choice([0.12, -0.12]) # >10% change
                    state_id = 4

                new_weight = round(animal['weight'] + fluctuation, 2)
                animal['weight'] = new_weight
                recorded_by = random.choice(working_employees)
                
                f.write(f"INSERT INTO animal_state_record VALUES ({record_id_counter}, {animal['id']}, '{date_str}', {new_weight}, {state_id}, {recorded_by});\n")
                record_id_counter += 1

    f.close()
    print(f"SQL 生成完畢 -> {filename}")
    print(f"  - 員工數: {len(used_employee_names)}")
    print(f"  - 動物數: {len(used_animal_names)}")
    print(f"  - 餵食紀錄: {feeding_id_counter-1}")
    print(f"  - 庫存紀錄: {stock_entry_id_counter-1}")
    print(f"  - 排班紀錄: {shift_id_counter-1}")

if __name__ == "__main__":
    generate_full_sql()