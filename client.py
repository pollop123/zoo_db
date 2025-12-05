import sys
import socket
import json
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, FloatPrompt, IntPrompt
from rich.panel import Panel
from rich.layout import Layout
from rich import print as rprint
from config import *

# Configuration
HOST = '127.0.0.1'
PORT = 60000

class NetworkClient:
    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.socket = None
        self.connected = False

    def connect(self):
        """建立長連線"""
        if self.connected:
            return True
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except ConnectionRefusedError:
            self.connected = False
            return False
        except Exception as e:
            self.connected = False
            return False

    def disconnect(self):
        """關閉連線"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.socket = None
        self.connected = False

    def send_request(self, action, data=None):
        """
        Send a JSON request to the server and return the JSON response.
        使用長連線，斷線時自動重連。
        """
        if data is None:
            data = {}
        
        request = {
            "action": action,
            "data": data
        }
        
        # 確保連線
        if not self.connected:
            if not self.connect():
                return {"success": False, "message": "無法連線至伺服器，請確認 Server 是否已啟動。"}
        
        try:
            # 發送請求
            request_json = json.dumps(request, default=str) + "\n"  # 加換行符作為訊息結尾
            self.socket.sendall(request_json.encode('utf-8'))
            
            # 接收回應
            response_data = ""
            while True:
                chunk = self.socket.recv(16384).decode('utf-8')
                if not chunk:
                    # 連線被關閉
                    self.connected = False
                    return {"success": False, "message": "伺服器連線中斷"}
                response_data += chunk
                if response_data.endswith("\n"):
                    break
            
            return json.loads(response_data.strip())
            
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            # 連線中斷，嘗試重連一次
            self.connected = False
            if self.connect():
                return self.send_request(action, data)  # 重試
            return {"success": False, "message": "連線中斷，重連失敗"}
        except Exception as e:
            self.connected = False
            return {"success": False, "message": f"網路錯誤: {e}"}


console = Console()
client = NetworkClient()

# 返回標記
BACK = "__BACK__"

def prompt_with_back(message, **kwargs):
    """帶有返回功能的輸入提示，輸入 'b' 或 'back' 返回上一頁"""
    hint = f"{message} [dim](輸入 b 返回)[/dim]"
    value = Prompt.ask(hint, **kwargs)
    if value.lower() in ['b', 'back', '返回']:
        return BACK
    return value

def float_prompt_with_back(message):
    """帶有返回功能的數字輸入"""
    hint = f"{message} [dim](輸入 b 返回)[/dim]"
    while True:
        value = Prompt.ask(hint)
        if value.lower() in ['b', 'back', '返回']:
            return BACK
        try:
            return float(value)
        except ValueError:
            console.print("[red]請輸入有效數字[/red]")

def select_my_animal(user_id):
    """選擇目前值班負責的動物，回傳 (a_id, a_name, species) 或 BACK"""
    response = client.send_request("get_my_animals", {"e_id": user_id})
    animals = response.get("data", [])
    
    if not animals:
        console.print("[yellow]你目前沒有負責任何動物[/yellow]")
        console.print("[dim]請確認班表或聯繫管理員[/dim]")
        return BACK
    
    # 顯示動物清單
    console.print("\n[bold cyan]你目前負責的動物：[/bold cyan]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("ID", style="cyan")
    table.add_column("名稱", style="green")
    table.add_column("物種", style="yellow")
    
    for i, (a_id, a_name, species) in enumerate(animals, 1):
        table.add_row(str(i), a_id, a_name or "-", species)
    
    console.print(table)
    
    # 選擇
    choice = prompt_with_back("請選擇動物 (輸入編號)")
    if choice == BACK:
        return BACK
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(animals):
            selected = animals[idx]
            console.print(f"[green]已選擇: {selected[1]} ({selected[2]})[/green]")
            return selected  # (a_id, a_name, species)
        else:
            console.print("[red]無效的選擇[/red]")
            return BACK
    except ValueError:
        # 允許直接輸入 ID
        for animal in animals:
            if animal[0].upper() == choice.upper():
                console.print(f"[green]已選擇: {animal[1]} ({animal[2]})[/green]")
                return animal
        console.print("[red]無效的選擇[/red]")
        return BACK

def forgot_password_screen():
    """忘記密碼功能"""
    console.print("\n[bold yellow]忘記密碼[/bold yellow]")
    e_id = Prompt.ask("請輸入員工 ID 以查詢密碼")
    
    response = client.send_request("forgot_password", {"e_id": e_id})
    
    if response.get("success"):
        name = response.get("name")
        password = response.get("password")
        console.print("─" * 30)
        console.print(f"員工: [cyan]{name}[/cyan] ({e_id})")
        console.print(f"密碼: [green]{password}[/green]")
        console.print("─" * 30)
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def login_screen():
    console.clear()
    console.print(Panel.fit("動物園管理系統 (Zoo Management System)", style="bold blue"))
    
    while True:
        e_id = Prompt.ask("請輸入員工 ID [dim](q: 離開, f: 忘記密碼)[/dim]")
        
        if e_id.lower() in ['q', 'quit', 'exit']:
            sys.exit()
        
        if e_id.lower() == 'f':
            forgot_password_screen()
            continue
            
        password = Prompt.ask("請輸入密碼", password=True)
        
        response = client.send_request("login", {"e_id": e_id, "password": password})
        
        if response.get("success"):
            name = response.get("name")
            role = response.get("role")
            console.print(f"[green]歡迎回來, {name} ({role})![/green]")
            return e_id, name, role
        else:
            console.print(f"[red]{response.get('message', '登入失敗')}[/red]")

def show_user_menu(user_id, name):
    while True:
        console.print("\n[bold cyan]使用者選單 (User Menu)[/bold cyan]")
        console.print("1. [新增餵食] Add Feeding Record")
        console.print("2. [新增身體資訊] Add Body Info (Weight)")
        console.print("3. [查詢班表] View Schedule")
        console.print("4. [查詢代碼表] View Reference Data")
        console.print("5. [修正自己紀錄] Correct My Record")

        console.print("6. [查詢個別動物趨勢] View Animal Trends")
        console.print("0. 登出 (Logout)")
        
        choice = Prompt.ask("請選擇功能", choices=["1", "2", "3", "4", "5", "6", "0"])
        
        if choice == "1":
            add_feeding_ui(user_id)
        elif choice == "2":
            add_body_info_ui(user_id)
        elif choice == "3":
            view_schedule_ui(user_id)
        elif choice == "4":
            view_reference_data_ui()
        elif choice == "5":
            correct_record_ui(user_id)
        elif choice == "6":
            view_animal_trends_ui()
        elif choice == "0":
            break

def show_admin_menu(user_id, name):
    while True:
        console.print("\n[bold magenta]管理員選單 (Admin Menu)[/bold magenta]")
        console.print("1. [修正紀錄稽核] View Audit Logs")
        console.print("2. [批量異常掃描] Batch Anomaly Scan (All Animals)")
        console.print("3. [庫存報表] View Inventory Report")
        console.print("4. [庫存進貨] Restock Inventory")
        console.print("5. [指派工作] Assign Task/Shift")
        console.print("6. [修正紀錄] Correct Record (Admin Override)")
        console.print("7. [高風險動物] View High Risk Animals")
        console.print("8. [查詢個別動物趨勢] View Animal Trends")
        console.print("9. [查詢代碼表] View Reference Data")
        console.print("10. [冒失鬼名單] View Careless Employees")
        console.print("11. [管理員工證照] Manage Employee Skills")
        console.print("12. [飲食管理] Manage Animal Diet")
        console.print("0. 登出 (Logout)")
        
        choice = Prompt.ask("請選擇功能", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "0"])
        
        if choice == "1":
            view_audit_logs_ui()
        elif choice == "2":
            batch_check_anomalies_ui()
        elif choice == "3":
            view_inventory_report_ui()
        elif choice == "4":
            restock_inventory_ui(user_id)
        elif choice == "5":
            assign_task_ui(user_id)
        elif choice == "6":
            correct_record_ui(user_id)
        elif choice == "7":
            view_high_risk_animals_ui()
        elif choice == "8":
            view_animal_trends_ui()
        elif choice == "9":
            view_reference_data_ui()
        elif choice == "10":
            view_careless_employees_ui()
        elif choice == "11":
            manage_skills_ui()
        elif choice == "12":
            manage_diet_ui()
        elif choice == "0":
            break

def manage_skills_ui():
    console.print("[bold]管理員工證照[/bold]")
    
    target_e_id = prompt_with_back("請輸入員工 ID")
    if target_e_id == BACK:
        return
    
    console.print("\n[bold]可用證照列表:[/bold]")
    console.print("1. Carnivore (猛獸專家)")
    console.print("2. Penguin (企鵝專家)")
    console.print("3. Endangered (珍稀動物專家)")
    
    choice = prompt_with_back("請選擇證照代號 (1-3)")
    if choice == BACK:
        return
    
    skill_map = {
        "1": "Carnivore",
        "2": "Penguin",
        "3": "Endangered"
    }
    
    if choice not in skill_map:
        console.print("[red]無效的選擇[/red]")
        return
    
    skill_name = skill_map[choice]
    
    response = client.send_request("add_employee_skill", {
        "target_e_id": target_e_id,
        "skill_name": skill_name
    })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def manage_diet_ui():
    """飲食管理 (Admin)"""
    while True:
        console.print("\n[bold]飲食管理[/bold]")
        console.print("1. 查看所有飲食設定")
        console.print("2. 查看特定物種飲食")
        console.print("3. 新增可食用飼料")
        console.print("4. 移除可食用飼料")
        console.print("0. 返回")
        
        choice = Prompt.ask("請選擇", choices=["1", "2", "3", "4", "0"])
        
        if choice == "1":
            # 查看所有飲食設定
            response = client.send_request("get_all_diet_settings", {})
            data = response.get("data", [])
            if not data:
                console.print("[yellow]尚無飲食設定[/yellow]")
                continue
            
            table = Table(title="所有物種飲食設定")
            table.add_column("物種", style="cyan")
            table.add_column("飼料 ID", style="yellow")
            table.add_column("飼料名稱", style="green")
            table.add_column("類別", style="dim")
            
            for species, f_id, feed_name, category in data:
                table.add_row(species, f_id, feed_name, category)
            console.print(table)
            
        elif choice == "2":
            # 查看特定物種
            species = prompt_with_back("請輸入物種名稱 (例如: Lion)")
            if species == BACK:
                continue
            
            response = client.send_request("get_animal_diet", {"species": species})
            feeds = response.get("data", [])
            
            if not feeds:
                console.print(f"[yellow]{species} 尚無飲食設定[/yellow]")
                continue
            
            table = Table(title=f"{species} 可食用飼料")
            table.add_column("飼料 ID", style="cyan")
            table.add_column("飼料名稱", style="green")
            table.add_column("類別", style="yellow")
            
            for f_id, feed_name, category in feeds:
                table.add_row(f_id, feed_name, category)
            console.print(table)
            
        elif choice == "3":
            # 新增飼料
            # 先顯示物種列表
            response = client.send_request("get_all_species", {})
            species_list = response.get("data", [])
            console.print("\n[bold]可用物種:[/bold]")
            for i, s in enumerate(species_list, 1):
                console.print(f"  {i}. {s}")
            
            species = prompt_with_back("請輸入物種名稱")
            if species == BACK:
                continue
            
            # 顯示所有飼料
            response = client.send_request("get_all_feeds", {})
            feeds = response.get("data", [])
            console.print("\n[bold]可用飼料:[/bold]")
            table = Table()
            table.add_column("ID", style="cyan")
            table.add_column("名稱", style="green")
            table.add_column("類別", style="yellow")
            for f_id, name, cat in feeds:
                table.add_row(f_id, name, cat)
            console.print(table)
            
            f_id = prompt_with_back("請輸入飼料 ID")
            if f_id == BACK:
                continue
            
            response = client.send_request("add_diet", {"species": species, "f_id": f_id})
            if response.get("success"):
                console.print(f"[green]{response.get('message')}[/green]")
            else:
                console.print(f"[red]{response.get('message')}[/red]")
            
        elif choice == "4":
            # 移除飼料
            species = prompt_with_back("請輸入物種名稱")
            if species == BACK:
                continue
            
            # 顯示目前該物種的飼料
            response = client.send_request("get_animal_diet", {"species": species})
            feeds = response.get("data", [])
            
            if not feeds:
                console.print(f"[yellow]{species} 尚無飲食設定[/yellow]")
                continue
            
            console.print(f"\n[bold]{species} 目前可食用:[/bold]")
            for f_id, name, cat in feeds:
                console.print(f"  {f_id} - {name} ({cat})")
            
            f_id = prompt_with_back("請輸入要移除的飼料 ID")
            if f_id == BACK:
                continue
            
            response = client.send_request("remove_diet", {"species": species, "f_id": f_id})
            if response.get("success"):
                console.print(f"[green]{response.get('message')}[/green]")
            else:
                console.print(f"[red]{response.get('message')}[/red]")
            
        elif choice == "0":
            break

def select_feed_for_animal(species):
    """選擇該物種可食用的飼料，回傳 f_id 或 BACK"""
    response = client.send_request("get_animal_diet", {"species": species})
    feeds = response.get("data", [])
    
    if not feeds:
        console.print(f"[yellow]{species} 尚未設定可食用飼料，請聯繫管理員[/yellow]")
        return BACK
    
    console.print(f"\n[bold cyan]{species} 可食用的飼料：[/bold cyan]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("ID", style="cyan")
    table.add_column("飼料名稱", style="green")
    table.add_column("類別", style="yellow")
    
    for i, (f_id, feed_name, category) in enumerate(feeds, 1):
        table.add_row(str(i), f_id, feed_name, category)
    
    console.print(table)
    
    choice = prompt_with_back("請選擇飼料 (輸入編號)")
    if choice == BACK:
        return BACK
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(feeds):
            return feeds[idx][0]  # f_id
        else:
            console.print("[red]無效的選擇[/red]")
            return BACK
    except ValueError:
        # 允許直接輸入 f_id
        for feed in feeds:
            if feed[0].upper() == choice.upper():
                return feed[0]
        console.print("[red]無效的選擇[/red]")
        return BACK

def add_feeding_ui(user_id):
    console.print("[bold]新增餵食紀錄[/bold]")
    
    # 選擇負責的動物
    animal = select_my_animal(user_id)
    if animal == BACK:
        return
    
    a_id, a_name, species = animal
    
    # [UX] Show recent records
    response = client.send_request("get_recent_records", {"table_name": TABLE_FEEDING, "filter_id": a_id})
    records = response.get("data", [])
    if records:
        r_table = Table(title=f"{a_name} ({species}) 的最近餵食紀錄")
        r_table.add_column("日期", style="cyan")
        r_table.add_column("飼料", style="yellow")
        r_table.add_column("數量 (kg)", style="green")
        for r in records[:3]: # Show top 3
            r_table.add_row(str(r[1]), r[2], str(r[3]))
        console.print(r_table)
    
    # 選擇該動物可食用的飼料
    f_id = select_feed_for_animal(species)
    if f_id == BACK:
        return
    
    amount = float_prompt_with_back("請輸入數量 (kg)")
    if amount == BACK:
        return
    
    if amount <= 0:
        console.print("[red]數量必須大於 0[/red]")
        return
        
    response = client.send_request("add_feeding", {
        "a_id": a_id, "f_id": f_id, "amount": amount, "user_id": user_id
    })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")


def add_body_info_ui(user_id):
    console.print("[bold]新增身體資訊[/bold]")
    
    # 選擇負責的動物
    animal = select_my_animal(user_id)
    if animal == BACK:
        return
    
    a_id, a_name, species = animal
    
    # [UX] Show recent records
    response = client.send_request("get_recent_records", {"table_name": TABLE_ANIMAL_STATE, "filter_id": a_id})
    records = response.get("data", [])
    if records:
        r_table = Table(title=f"{a_name} ({species}) 的最近體重紀錄")
        r_table.add_column("日期", style="cyan")
        r_table.add_column("體重 (kg)", style="green")
        for r in records[:3]: # Show top 3
            r_table.add_row(str(r[1]), str(r[2]))
        console.print(r_table)
    
    weight = float_prompt_with_back("請輸入體重 (kg)")
    if weight == BACK:
        return
    
    if weight <= 0:
        console.print("[red]體重必須大於 0[/red]")
        return
        
    # [NEW] Select Status
    state_id = 1 # Default Normal
    resp_status = client.send_request("get_reference_data", {"table_name": "status_type"})
    if resp_status.get("success"):
        statuses = resp_status.get("data", [])
        if statuses:
            console.print("\n[bold]請選擇動物狀態:[/bold]")
            for s in statuses:
                console.print(f"{s[0]}. {s[1]} ({s[2]})")
            
            state_input = prompt_with_back("請輸入狀態 ID (預設 1)")
            if state_input == BACK:
                return
            if state_input:
                try:
                    state_id = int(state_input)
                except ValueError:
                    state_id = 1

    response = client.send_request("add_animal_state", {
        "a_id": a_id, "weight": weight, "user_id": user_id, "state_id": state_id
    })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def view_schedule_ui(user_id):
    console.print("[bold]我的班表[/bold]")
    response = client.send_request("get_employee_schedule", {"e_id": user_id})
    schedule = response.get("data", [])
    
    if not schedule:
        console.print("[yellow]查無近期班表。[/yellow]")
        return

    table = Table(title="我的班表")
    table.add_column("開始時間", style="cyan")
    table.add_column("結束時間", style="cyan")
    table.add_column("工作項目", style="green")
    table.add_column("負責動物", style="yellow")

    for row in schedule:
        # row[3] is a_id, might be None
        a_id = row[3] if row[3] else "-"
        table.add_row(str(row[0]), str(row[1]), row[2], a_id)
    
    console.print(table)

def assign_task_ui(user_id):
    console.print("[bold]指派工作 / 排班[/bold]")
    
    target_e_id = prompt_with_back("請輸入目標員工 ID")
    if target_e_id == BACK:
        return
    
    t_id = prompt_with_back("請輸入工作 ID")
    if t_id == BACK:
        return
    
    start_time = prompt_with_back("請輸入開始時間 (YYYY-MM-DD HH:MM:SS)")
    if start_time == BACK:
        return
    
    end_time = prompt_with_back("請輸入結束時間 (YYYY-MM-DD HH:MM:SS)")
    if end_time == BACK:
        return
    
    # Optional a_id
    a_id = prompt_with_back("請輸入負責動物 ID (選填, 若無請直接 Enter)")
    if a_id == BACK:
        return
    if a_id == "": 
        a_id = None
    
    response = client.send_request("assign_task", {
        "e_id": target_e_id, "t_id": t_id, "start_time": start_time, "end_time": end_time, "a_id": a_id
    })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def restock_inventory_ui(user_id):
    console.print("[bold]庫存進貨[/bold]")
    
    f_id = prompt_with_back("請輸入飼料 ID")
    if f_id == BACK:
        return
    
    amount = float_prompt_with_back("請輸入數量 (kg)")
    if amount == BACK:
        return
    
    if amount <= 0 or amount >= 100000:
        console.print("[red]數量必須大於 0 且小於 100,000[/red]")
        return
        
    response = client.send_request("add_inventory_stock", {
        "f_id": f_id, "amount": amount, "user_id": user_id
    })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def correct_record_ui(user_id):
    console.print("[bold]修正紀錄[/bold]")
    
    table_map = {
        "1": TABLE_FEEDING,
        "2": TABLE_ANIMAL_STATE
    }
    console.print("請選擇資料表:")
    console.print(f"1. {TABLE_FEEDING} (餵食紀錄)")
    console.print(f"2. {TABLE_ANIMAL_STATE} (動物狀態)")
    
    t_choice = prompt_with_back("選擇 (1-2)")
    if t_choice == BACK:
        return
    if t_choice not in table_map:
        console.print("[red]無效的選擇[/red]")
        return
    table = table_map[t_choice]
    
    # Step 1: Filter by Animal ID to find records
    a_id = prompt_with_back("請輸入動物 ID 以搜尋紀錄")
    if a_id == BACK:
        return
    
    response = client.send_request("get_recent_records", {
        "table_name": table, "filter_id": a_id
    })
    records = response.get("data", [])
    
    if not records:
        console.print("[yellow]查無此動物的近期紀錄。[/yellow]")
        return

    # Display Records
    r_table = Table(title=f"動物 {a_id} 的近期紀錄")
    r_table.add_column("紀錄 ID", style="cyan")
    r_table.add_column("日期", style="blue")
    
    if table == TABLE_FEEDING:
        r_table.add_column("飼料", style="yellow")
        r_table.add_column("數量", style="green")
        for r in records:
            r_table.add_row(str(r[0]), str(r[1]), r[2], str(r[3]))
    else:
        r_table.add_column("體重", style="green")
        for r in records:
            r_table.add_row(str(r[0]), str(r[1]), str(r[2]))
            
    console.print(r_table)
    
    # Step 2: Select Record ID
    record_id = prompt_with_back("請輸入要修正的紀錄 ID (參考上表)")
    if record_id == BACK:
        return
    
    col_choice = ""
    col_name = ""
    
    if table == TABLE_FEEDING:
        console.print("請選擇要修正的欄位:")
        console.print(f"1. {COL_AMOUNT} (餵食量)")
        col_choice = prompt_with_back("選擇")
        if col_choice == BACK:
            return
        if col_choice == "1": 
            col_name = COL_AMOUNT
        else:
            console.print("[red]無效的選擇[/red]")
            return
        
    elif table == TABLE_ANIMAL_STATE:
        # Only one choice, auto-select
        col_name = COL_WEIGHT

    new_val = float_prompt_with_back(f"請輸入 {col_name} 的正確數值")
    if new_val == BACK:
        return
    
    response = client.send_request("correct_record", {
        "user_id": user_id, "table": table, "record_id": record_id, 
        "col_name": col_name, "new_val": new_val
    })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def view_audit_logs_ui():
    response = client.send_request("get_audit_logs")
    logs = response.get("data", [])
    
    if not logs:
        console.print("[yellow]查無稽核紀錄。[/yellow]")
        return

    table = Table(title="稽核日誌 (Audit Logs - NoSQL)")
    table.add_column("時間", style="cyan")
    table.add_column("操作者 ID", style="magenta")
    table.add_column("資料表", style="green")
    table.add_column("變更內容", style="white")

    for log in logs:
        change_str = f"{log['change']['field']}: {log['change']['old_value']} -> {log['change']['new_value']}"
        table.add_row(log['timestamp'], str(log['operator_id']), log['target_table'], change_str)
    
    console.print(table)

# def check_anomalies_ui():  <-- Removed as integrated into view_animal_trends_ui


def batch_check_anomalies_ui():
    console.print("[bold]批量異常掃描[/bold]")
    console.print("正在掃描全園區動物... 請稍候。")
    
    response = client.send_request("batch_check_anomalies")
    anomalies = response.get("data", [])
    
    if not anomalies:
        console.print("[green]掃描完成。未發現異常。[/green]")
        return

    console.print(f"[red]掃描完成。發現 {len(anomalies)} 筆異常！[/red]")
    
    table = Table(title="偵測到的異常")
    table.add_column("動物 ID", style="cyan")
    table.add_column("名字", style="yellow")
    table.add_column("變化率 %", style="red")
    table.add_column("訊息", style="white")
    
    for a in anomalies:
        table.add_row(str(a['id']), a['name'], f"{a['pct']:.1f}%", a['msg'])
        
    console.print(table)
    console.print("[bold red]所有警示已寫入 NoSQL。[/bold red]")

def view_high_risk_animals_ui():
    response = client.send_request("get_high_risk_animals")
    results = response.get("data", [])
    
    if not results:
        console.print("[green]未發現高風險動物 (異常次數 < 3)。[/green]")
        return

    table = Table(title="高風險動物 (異常次數 >= 3)")
    table.add_column("動物 ID", style="red")
    table.add_column("異常次數", style="yellow")

    for res in results:
        table.add_row(str(res['_id']), str(res['count']))
    
    console.print(table)

def view_careless_employees_ui():
    response = client.send_request("get_careless_employees")
    results = response.get("data", [])
    
    if not results:
        console.print("[green]未發現冒失鬼 (修正次數 < 5)。[/green]")
        return

    table = Table(title="冒失鬼名單 (修正次數 >= 5)")
    table.add_column("員工 ID", style="red")
    table.add_column("姓名", style="yellow")
    table.add_column("修正次數", style="white")

    for res in results:
        table.add_row(str(res['id']), res['name'], str(res['count']))
    
    console.print(table)

def view_inventory_report_ui():
    response = client.send_request("get_inventory_report")
    data = response.get("data", [])
    
    if not data:
        console.print("[yellow]查無庫存資料。[/yellow]")
        return

    table = Table(title="庫存報表")
    table.add_column("飼料名稱", style="cyan")
    table.add_column("目前庫存 (kg)", style="green")

    for row in data:
        table.add_row(row[0], str(row[1]))
    
    console.print(table)

def view_animal_trends_ui():
    console.print("[bold]查詢個別動物趨勢[/bold]")
    
    a_id = prompt_with_back("請輸入動物 ID")
    if a_id == BACK:
        return
    
    response = client.send_request("get_animal_trends", {"a_id": a_id})
    weights = response.get("weights", [])
    feedings = response.get("feedings", [])
    
    if weights:
        w_table = Table(title=f"近期體重 (動物 {a_id})")
        w_table.add_column("日期", style="cyan")
        w_table.add_column("體重 (kg)", style="green")
        for w in weights:
            w_table.add_row(str(w[0]), str(w[1]))
        console.print(w_table)
    else:
        console.print("[yellow]查無體重紀錄。[/yellow]")

    if feedings:
        f_table = Table(title=f"近期餵食 (動物 {a_id})")
        f_table.add_column("日期", style="cyan")
        f_table.add_column("飼料", style="yellow")
        f_table.add_column("數量 (kg)", style="white")
        for f in feedings:
            f_table.add_row(str(f[0]), f[1], str(f[2]))
        console.print(f_table)
    else:
        console.print("[yellow]查無餵食紀錄。[/yellow]")

    # [Integrated] Check Anomaly automatically
    console.print("\n[bold]正在進行異常檢查...[/bold]")
    response = client.send_request("check_weight_anomaly", {"a_id": a_id})
    success = response.get("success")
    msg = response.get("message")
    
    if success:
        console.print(f"[red]警示: {msg}[/red]")
        console.print("[bold red]已自動記錄至系統警示。[/bold red]")
    else:
        console.print(f"[green]檢查結果: {msg}[/green]")

def view_reference_data_ui():
    console.print("[bold]查詢代碼表[/bold]")
    console.print("1. 動物 (Animals)")
    console.print("2. 飼料 (Feeds)")
    console.print("3. 工作 (Tasks)")
    console.print("4. 員工 (Employees)")
    
    choice = prompt_with_back("請選擇資料表 (1-4)")
    if choice == BACK:
        return
    if choice not in ["1", "2", "3", "4"]:
        console.print("[red]無效的選擇[/red]")
        return
    
    table_name = ""
    title = ""
    if choice == "1": 
        table_name = "animal"
        title = "動物列表"
    elif choice == "2": 
        table_name = "feeds"
        title = "飼料列表"
    elif choice == "3": 
        table_name = "task"
        title = "工作列表"
    elif choice == "4":
        table_name = "employee"
        title = "員工列表"
        
    response = client.send_request("get_reference_data", {"table_name": table_name})
    data = response.get("data", [])
    
    if not data:
        console.print("[yellow]查無資料。[/yellow]")
        return

    table = Table(title=title)
    if choice == "1":
        table.add_column("ID", style="cyan")
        table.add_column("名稱", style="green")
        table.add_column("物種", style="yellow")
        for row in data:
            table.add_row(str(row[0]), row[1], row[2])
    elif choice == "2":
        table.add_column("ID", style="cyan")
        table.add_column("名稱", style="green")
        table.add_column("分類", style="yellow")
        for row in data:
            table.add_row(str(row[0]), row[1], row[2])
    elif choice == "3":
        table.add_column("ID", style="cyan")
        table.add_column("名稱", style="green")
        for row in data:
            table.add_row(str(row[0]), row[1])
    elif choice == "4":
        table.add_column("ID", style="cyan")
        table.add_column("姓名", style="green")
        table.add_column("角色", style="magenta")
        for row in data:
            table.add_row(str(row[0]), row[1], row[2])
            
    console.print(table)

def main():
    while True:
        try:
            user_id, name, role = login_screen()
            
            if role.lower() == "admin":
                show_admin_menu(user_id, name)
            else:
                show_user_menu(user_id, name)
                
        except KeyboardInterrupt:
            console.print("\n[bold]再見![/bold]")
            client.disconnect()  # 優雅關閉連線
            sys.exit()

if __name__ == "__main__":
    main()
