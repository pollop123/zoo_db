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
        console.print("4. [修正自己紀錄] Correct My Record")
        console.print("5. [修改密碼] Change Password")
        console.print("6. [我的修正紀錄] View My Corrections")
        console.print("0. 登出 (Logout)")
        
        choice = Prompt.ask("請選擇功能", choices=["1", "2", "3", "4", "5", "6", "0"])
        
        if choice == "1":
            add_feeding_ui(user_id)
        elif choice == "2":
            add_body_info_ui(user_id)
        elif choice == "3":
            view_schedule_ui(user_id)
        elif choice == "4":
            correct_record_ui(user_id)
        elif choice == "5":
            change_password_ui(user_id)
        elif choice == "6":
            view_my_corrections_ui(user_id)
        elif choice == "0":
            break

def show_admin_menu(user_id, name):
    while True:
        console.print("\n[bold magenta]管理員選單 (Admin Menu)[/bold magenta]")
        console.print("1. [稽核日誌] View Audit Logs")
        console.print("2. [健康監控] Health Monitor (Anomaly + Risk)")
        console.print("3. [庫存管理] Inventory Management")
        console.print("4. [指派工作] Assign Task/Shift")
        console.print("5. [修正紀錄] Correct Record")
        console.print("6. [冒失鬼名單] View Careless Employees")
        console.print("7. [員工管理] Manage Employees")
        console.print("8. [飲食管理] Manage Animal Diet")
        console.print("9. [查詢動物趨勢] View Animal Trends")
        console.print("0. 登出 (Logout)")
        
        choice = Prompt.ask("請選擇功能", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])
        
        if choice == "1":
            view_audit_logs_ui()
        elif choice == "2":
            health_monitor_ui()
        elif choice == "3":
            inventory_management_ui(user_id)
        elif choice == "4":
            assign_task_ui(user_id)
        elif choice == "5":
            correct_record_ui(user_id)
        elif choice == "6":
            view_careless_employees_ui()
        elif choice == "7":
            manage_employees_ui()
        elif choice == "8":
            manage_diet_ui()
        elif choice == "9":
            view_animal_trends_ui()
        elif choice == "0":
            break

def health_monitor_ui():
    """健康監控 (合併：批量異常掃描 + 高風險動物)"""
    while True:
        console.print("\n[bold]健康監控[/bold]")
        console.print("1. 批量異常掃描 (所有動物)")
        console.print("2. 高風險動物列表")
        console.print("3. 查詢個別動物趨勢")
        console.print("4. 待處理健康警示")
        console.print("0. 返回")
        
        choice = Prompt.ask("請選擇", choices=["1", "2", "3", "4", "0"])
        
        if choice == "1":
            batch_check_anomalies_ui()
        elif choice == "2":
            view_high_risk_animals_ui()
        elif choice == "3":
            view_animal_trends_ui()
        elif choice == "4":
            view_pending_health_alerts_ui()
        elif choice == "0":
            break

def inventory_management_ui(user_id):
    """庫存管理 (合併：庫存報表 + 庫存進貨)"""
    while True:
        console.print("\n[bold]庫存管理[/bold]")
        console.print("1. 查看庫存報表")
        console.print("2. 庫存進貨")
        console.print("0. 返回")
        
        choice = Prompt.ask("請選擇", choices=["1", "2", "0"])
        
        if choice == "1":
            view_inventory_report_ui()
        elif choice == "2":
            restock_inventory_ui(user_id)
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

def change_password_ui(user_id):
    """修改密碼 (User)"""
    console.print("[bold]修改密碼[/bold]")
    
    old_password = Prompt.ask("請輸入舊密碼", password=True)
    new_password = Prompt.ask("請輸入新密碼", password=True)
    confirm_password = Prompt.ask("請再次輸入新密碼", password=True)
    
    if new_password != confirm_password:
        console.print("[red]兩次輸入的新密碼不一致[/red]")
        return
    
    if len(new_password) < 4:
        console.print("[red]密碼長度至少 4 個字元[/red]")
        return
    
    response = client.send_request("change_password", {
        "e_id": user_id,
        "old_password": old_password,
        "new_password": new_password
    })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def view_my_corrections_ui(user_id):
    """飼養員查看自己被修正的紀錄"""
    console.print("[bold]我的修正紀錄[/bold]")
    
    response = client.send_request("get_my_corrections", {"e_id": user_id})
    data = response.get("data", {})
    
    careless = data.get("careless", [])
    corrections = data.get("corrections", [])
    
    if not careless and not corrections:
        console.print("[green]你沒有任何被修正的紀錄，做得很好！[/green]")
        return
    
    # 顯示輸入錯誤紀錄 (careless_logs)
    if careless:
        table = Table(title="輸入錯誤紀錄 (已被標記)")
        table.add_column("動物 ID", style="red")
        table.add_column("錯誤類型", style="yellow")
        table.add_column("錯誤值", style="white")
        table.add_column("時間", style="dim")
        
        for c in careless:
            table.add_row(
                c.get("animal_id", ""),
                c.get("error_type", ""),
                str(c.get("wrong_value", "")),
                str(c.get("original_timestamp", ""))[:19] if c.get("original_timestamp") else ""
            )
        console.print(table)
    
    # 顯示被管理員修正的紀錄 (audit_logs)
    if corrections:
        table2 = Table(title="被管理員修正的紀錄")
        table2.add_column("資料表", style="blue")
        table2.add_column("欄位", style="yellow")
        table2.add_column("舊值 -> 新值", style="white")
        table2.add_column("修正時間", style="dim")
        
        for c in corrections:
            change = c.get("change", {})
            change_str = f"{change.get('old_value', '')} -> {change.get('new_value', '')}"
            table2.add_row(
                c.get("target_table", ""),
                change.get("field", ""),
                change_str,
                str(c.get("timestamp", ""))[:19] if c.get("timestamp") else ""
            )
        console.print(table2)

def manage_employees_ui():
    """員工管理 (Admin) - 合併證照管理"""
    while True:
        console.print("\n[bold]員工管理[/bold]")
        console.print("1. 查看所有員工")
        console.print("2. 新增員工")
        console.print("3. 停用/啟用員工")
        console.print("4. 變更員工角色")
        console.print("5. 管理員工證照")
        console.print("0. 返回")
        
        choice = Prompt.ask("請選擇", choices=["1", "2", "3", "4", "5", "0"])
        
        if choice == "1":
            # 查看所有員工
            response = client.send_request("get_all_employees", {})
            data = response.get("data", [])
            if not data:
                console.print("[yellow]無員工資料[/yellow]")
                continue
            
            table = Table(title="所有員工")
            table.add_column("員工 ID", style="cyan")
            table.add_column("姓名", style="green")
            table.add_column("角色", style="yellow")
            table.add_column("狀態", style="dim")
            
            for emp in data:
                e_id = emp.get("e_id", "")
                name = emp.get("e_name", "")
                role = emp.get("role", "")
                status = emp.get("e_status", "")
                status_style = "green" if status == "active" else "red"
                table.add_row(e_id, name, role, f"[{status_style}]{status}[/{status_style}]")
            console.print(table)
            
        elif choice == "2":
            # 新增員工
            e_id = prompt_with_back("請輸入員工 ID (例如: E999)")
            if e_id == BACK:
                continue
            
            name = prompt_with_back("請輸入姓名")
            if name == BACK:
                continue
            
            console.print("性別: 1. 男 (M)  2. 女 (F)")
            sex_choice = Prompt.ask("請選擇性別", choices=["1", "2"], default="1")
            sex = "M" if sex_choice == "1" else "F"
            
            console.print("角色: 1. User  2. Admin")
            role_choice = Prompt.ask("請選擇角色", choices=["1", "2"], default="1")
            role = "Admin" if role_choice == "2" else "User"
            
            response = client.send_request("add_employee", {"e_id": e_id, "name": name, "role": role, "sex": sex})
            if response.get("success"):
                console.print(f"[green]{response.get('message')}[/green]")
            else:
                console.print(f"[red]{response.get('message')}[/red]")
            
        elif choice == "3":
            # 停用/啟用員工
            e_id = prompt_with_back("請輸入員工 ID")
            if e_id == BACK:
                continue
            
            console.print("狀態: 1. active (啟用)  2. inactive (停用)")
            status_choice = Prompt.ask("請選擇狀態", choices=["1", "2"])
            status = "active" if status_choice == "1" else "inactive"
            
            response = client.send_request("update_employee_status", {"e_id": e_id, "status": status})
            if response.get("success"):
                console.print(f"[green]{response.get('message')}[/green]")
            else:
                console.print(f"[red]{response.get('message')}[/red]")
            
        elif choice == "4":
            # 變更角色
            e_id = prompt_with_back("請輸入員工 ID")
            if e_id == BACK:
                continue
            
            console.print("角色: 1. User  2. Admin")
            role_choice = Prompt.ask("請選擇新角色", choices=["1", "2"])
            role = "Admin" if role_choice == "2" else "User"
            
            response = client.send_request("update_employee_role", {"e_id": e_id, "role": role})
            if response.get("success"):
                console.print(f"[green]{response.get('message')}[/green]")
            else:
                console.print(f"[red]{response.get('message')}[/red]")
        
        elif choice == "5":
            # 管理證照
            manage_skills_ui()
            
        elif choice == "0":
            break

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
    
    # [即時警告] 檢查食量是否異常
    if records:
        recent_amounts = [r[3] for r in records[:5] if r[3] is not None]
        if recent_amounts:
            avg_amount = sum(recent_amounts) / len(recent_amounts)
            if avg_amount > 0:
                deviation = abs(amount - avg_amount) / avg_amount * 100
                if deviation > 50:  # 偏差超過 50%
                    console.print(f"\n[bold yellow]⚠ 警告：您輸入的食量 {amount} kg 與近期平均 {avg_amount:.2f} kg 差異 {deviation:.0f}%[/bold yellow]")
                    confirm = Prompt.ask("確定要儲存嗎？", choices=["y", "n"], default="n")
                    # 記錄警告事件
                    client.send_request("log_input_warning", {
                        "user_id": user_id, "animal_id": a_id, "warning_type": "FEEDING",
                        "input_value": amount, "expected_value": avg_amount, "confirmed": confirm.lower() == "y"
                    })
                    if confirm.lower() != "y":
                        console.print("[yellow]已取消輸入。[/yellow]")
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
    
    # [即時警告] 檢查體重是否異常
    if records:
        recent_weights = [r[2] for r in records[:5] if r[2] is not None]
        if recent_weights:
            last_weight = recent_weights[0]  # 最近一筆
            if last_weight > 0:
                change_pct = abs(weight - last_weight) / last_weight * 100
                if change_pct > 20:  # 單次變化超過 20%
                    console.print(f"\n[bold yellow]⚠ 警告：您輸入的體重 {weight} kg 與上次 {last_weight:.2f} kg 變化 {change_pct:.0f}%[/bold yellow]")
                    confirm = Prompt.ask("確定要儲存嗎？", choices=["y", "n"], default="n")
                    # 記錄警告事件
                    client.send_request("log_input_warning", {
                        "user_id": user_id, "animal_id": a_id, "warning_type": "WEIGHT",
                        "input_value": weight, "expected_value": last_weight, "confirmed": confirm.lower() == "y"
                    })
                    if confirm.lower() != "y":
                        console.print("[yellow]已取消輸入。[/yellow]")
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
    
    # 1. 選擇員工
    response = client.send_request("get_all_employees", {})
    if not response.get("success"):
        console.print(f"[red]{response.get('message')}[/red]")
        return
    
    employees = response.get("data", [])
    active_employees = [e for e in employees if e.get("e_status") == "active"]
    
    if not active_employees:
        console.print("[yellow]目前沒有可用員工[/yellow]")
        return
    
    console.print("\n[cyan]可選員工列表:[/cyan]")
    for i, emp in enumerate(active_employees, 1):
        role = emp.get("role", "User")
        console.print(f"  {i}. {emp['e_id']} - {emp['e_name']} ({role})")
    
    emp_choice = prompt_with_back(f"請選擇員工 (1-{len(active_employees)})")
    if emp_choice == BACK:
        return
    try:
        emp_idx = int(emp_choice) - 1
        if emp_idx < 0 or emp_idx >= len(active_employees):
            raise ValueError
        target_e_id = active_employees[emp_idx]["e_id"]
    except ValueError:
        console.print("[red]無效選擇[/red]")
        return
    
    # 2. 選擇工作類型
    response = client.send_request("get_all_tasks", {})
    if not response.get("success"):
        console.print(f"[red]{response.get('message')}[/red]")
        return
    
    tasks = response.get("data", [])
    if not tasks:
        console.print("[yellow]目前沒有工作類型[/yellow]")
        return
    
    console.print("\n[cyan]工作類型列表:[/cyan]")
    for i, task in enumerate(tasks, 1):
        console.print(f"  {i}. {task['t_id']} - {task['t_name']}")
    
    task_choice = prompt_with_back(f"請選擇工作類型 (1-{len(tasks)})")
    if task_choice == BACK:
        return
    try:
        task_idx = int(task_choice) - 1
        if task_idx < 0 or task_idx >= len(tasks):
            raise ValueError
        t_id = tasks[task_idx]["t_id"]
    except ValueError:
        console.print("[red]無效選擇[/red]")
        return
    
    # 3. 輸入時間
    from datetime import datetime, timedelta
    today = datetime.now().strftime("%Y-%m-%d")
    console.print(f"\n[dim]提示: 今天是 {today}[/dim]")
    
    start_time = prompt_with_back("請輸入開始時間 (YYYY-MM-DD HH:MM:SS)")
    if start_time == BACK:
        return
    
    end_time = prompt_with_back("請輸入結束時間 (YYYY-MM-DD HH:MM:SS)")
    if end_time == BACK:
        return
    
    # 4. 選擇動物 (選填)
    response = client.send_request("get_all_animals", {})
    animals = response.get("data", []) if response.get("success") else []
    
    a_id = None
    if animals:
        console.print("\n[cyan]可選動物列表 (選填):[/cyan]")
        console.print("  0. 不指派特定動物")
        for i, animal in enumerate(animals, 1):
            name = animal.get('a_name', '')
            species = animal.get('species', '')
            console.print(f"  {i}. {animal['a_id']} - {name} ({species})")
        
        animal_choice = prompt_with_back(f"請選擇動物 (0-{len(animals)})")
        if animal_choice == BACK:
            return
        try:
            animal_idx = int(animal_choice)
            if animal_idx > 0 and animal_idx <= len(animals):
                a_id = animals[animal_idx - 1]["a_id"]
        except ValueError:
            pass
    
    response = client.send_request("assign_task", {
        "e_id": target_e_id, "t_id": t_id, "start_time": start_time, "end_time": end_time, "a_id": a_id
    })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def restock_inventory_ui(user_id):
    console.print("[bold]庫存進貨[/bold]")
    
    # 取得飼料清單 (含目前庫存)
    response = client.send_request("get_inventory_report", {})
    if not response.get("success"):
        console.print(f"[red]{response.get('message')}[/red]")
        return
    
    inventory = response.get("data", [])
    if not inventory:
        console.print("[yellow]目前沒有飼料資料[/yellow]")
        return
    
    console.print("\n[cyan]飼料庫存列表:[/cyan]")
    for i, item in enumerate(inventory, 1):
        stock = item.get('current_stock', 0)
        unit = item.get('unit', 'kg')
        status = "[red](低庫存)[/red]" if stock < 50 else ""
        console.print(f"  {i}. {item['f_id']} - {item['f_name']}: {stock} {unit} {status}")
    
    choice = prompt_with_back(f"請選擇要進貨的飼料 (1-{len(inventory)})")
    if choice == BACK:
        return
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(inventory):
            raise ValueError
        f_id = inventory[idx]["f_id"]
        f_name = inventory[idx]["f_name"]
    except ValueError:
        console.print("[red]無效選擇[/red]")
        return
    
    console.print(f"\n[dim]已選擇: {f_name}[/dim]")
    amount = float_prompt_with_back("請輸入進貨數量 (kg)")
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
    table.add_column("操作者", style="magenta")
    table.add_column("操作類型", style="green")
    table.add_column("對象", style="yellow")
    table.add_column("變更內容", style="white")

    for log in logs:
        # 處理新格式 (DATA_CORRECTION)
        if 'change' in log and isinstance(log['change'], dict):
            action_type = log.get('event_type', 'DATA_CORRECTION')
            target = log.get('target_table', '') + ' / ' + str(log.get('record_id', ''))
            change_str = f"{log['change'].get('field', '')}: {log['change'].get('old_value', '')} -> {log['change'].get('new_value', '')}"
        # 處理舊格式 (action based)
        elif 'action' in log:
            action_type = log.get('description', log.get('action', ''))
            target = log.get('target_id', '')
            if log.get('old_value') and log.get('new_value'):
                change_str = f"{log['old_value']} -> {log['new_value']}"
            else:
                change_str = "-"
        else:
            action_type = log.get('event_type', 'N/A')
            target = log.get('target_id', 'N/A')
            change_str = str(log.get('details', '-'))
        
        timestamp = log.get('timestamp', log.get('created_at', 'N/A'))
        operator = str(log.get('operator_id', log.get('admin_id', 'N/A')))
        table.add_row(timestamp, operator, action_type, target, change_str)
    
    console.print(table)

# def check_anomalies_ui():  <-- Removed as integrated into view_animal_trends_ui


def batch_check_anomalies_ui():
    console.print("[bold]批量異常掃描 (體重 + 食量)[/bold]")
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
    table.add_column("類型", style="magenta")
    table.add_column("變化率 %", style="red")
    table.add_column("訊息", style="white")
    
    for a in anomalies:
        anomaly_type = a.get('type', '體重')
        table.add_row(str(a['id']), a['name'], anomaly_type, f"{a['pct']:.1f}%", a['msg'])
        
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

def view_pending_health_alerts_ui():
    """查看待處理的健康警示，管理員可確認或修正"""
    response = client.send_request("get_pending_health_alerts")
    alerts = response.get("data", [])
    
    if not alerts:
        console.print("[green]目前沒有待處理的健康警示。[/green]")
        return
    
    while True:
        table = Table(title="待處理健康警示 (PENDING)")
        table.add_column("#", style="cyan")
        table.add_column("動物 ID", style="red")
        table.add_column("動物名", style="yellow")
        table.add_column("警示類型", style="magenta")
        table.add_column("輸入值", style="white")
        table.add_column("輸入者", style="blue")
        table.add_column("時間", style="dim")
        
        for i, alert in enumerate(alerts, 1):
            # 支援兩種欄位名稱 (新舊格式相容)
            detected_val = alert.get("detected_value") or alert.get("input_value", "")
            recorded_by = alert.get("recorded_by") or alert.get("input_by", "")
            created_at = alert.get("created_at") or alert.get("timestamp", "")
            table.add_row(
                str(i),
                alert.get("animal_id", ""),
                alert.get("animal_name", ""),
                alert.get("alert_type", ""),
                str(detected_val),
                recorded_by,
                created_at[:19] if created_at else ""
            )
        
        console.print(table)
        console.print("\n[bold]處理選項:[/bold]")
        console.print("輸入編號 → 處理該筆警示")
        console.print("0 → 返回")
        
        choice = Prompt.ask("請選擇")
        if choice == "0":
            break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(alerts):
                handle_health_alert(alerts[idx])
                # 重新載入
                response = client.send_request("get_pending_health_alerts")
                alerts = response.get("data", [])
                if not alerts:
                    console.print("[green]所有警示已處理完畢。[/green]")
                    break
            else:
                console.print("[red]無效的編號[/red]")
        except ValueError:
            console.print("[red]請輸入數字[/red]")

def handle_health_alert(alert):
    """處理單一健康警示"""
    # 支援兩種欄位名稱 (新舊格式相容)
    detected_val = alert.get("detected_value") or alert.get("input_value", "")
    recorded_by = alert.get("recorded_by") or alert.get("input_by", "")
    created_at = alert.get("created_at") or alert.get("timestamp", "")
    
    console.print(f"\n[bold]處理警示: {alert.get('animal_id')} - {alert.get('animal_name', '')}[/bold]")
    console.print(f"警示類型: {alert.get('alert_type')}")
    console.print(f"輸入值: {detected_val}")
    console.print(f"輸入者: {recorded_by}")
    console.print(f"時間: {created_at[:19] if created_at else ''}")
    
    console.print("\n[bold]請選擇處理方式:[/bold]")
    console.print("1. 確認為真實健康問題 (保留警示)")
    console.print("2. 判定為輸入錯誤 (移至冒失鬼名單，請稍後去修正紀錄)")
    console.print("0. 取消")
    
    choice = Prompt.ask("請選擇", choices=["1", "2", "0"])
    
    if choice == "0":
        return
    
    if choice == "1":
        # 確認為真實健康問題
        response = client.send_request("confirm_health_alert", {
            "alert_id": alert.get("_id"),
            "status": "CONFIRMED"
        })
    elif choice == "2":
        # 判定為輸入錯誤
        response = client.send_request("confirm_health_alert", {
            "alert_id": alert.get("_id"),
            "status": "INPUT_ERROR"
        })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def view_careless_employees_ui():
    response = client.send_request("get_careless_employees")
    results = response.get("data", [])
    
    if not results:
        console.print("[green]目前沒有輸入錯誤紀錄。[/green]")
        return

    table = Table(title="冒失鬼名單 (輸入錯誤紀錄)")
    table.add_column("員工 ID", style="red")
    table.add_column("姓名", style="yellow")
    table.add_column("輸入錯誤", style="white")
    table.add_column("被修正次數", style="white")
    table.add_column("總計", style="bold red")

    for res in results:
        table.add_row(
            str(res['id']), 
            res['name'], 
            str(res.get('input_errors', 0)),
            str(res.get('corrections', 0)),
            str(res.get('total', 0))
        )
    
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
