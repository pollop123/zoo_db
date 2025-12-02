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

    def send_request(self, action, data=None):
        """
        Send a JSON request to the server and return the JSON response.
        """
        if data is None:
            data = {}
        
        request = {
            "action": action,
            "data": data
        }
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(json.dumps(request, default=str).encode('utf-8'))
                
                # Receive response (basic implementation, might need buffering for large data)
                # For this project, 16KB buffer should be enough for most lists
                response_data = s.recv(16384).decode('utf-8')
                
                if not response_data:
                    return {"success": False, "message": "伺服器回傳空值"}
                
                return json.loads(response_data)
        except ConnectionRefusedError:
            return {"success": False, "message": "無法連線至伺服器，請確認 Server 是否已啟動。"}
        except Exception as e:
            return {"success": False, "message": f"網路錯誤: {e}"}

console = Console()
client = NetworkClient()

def login_screen():
    console.clear()
    console.print(Panel.fit("動物園管理系統 (Zoo Management System)", style="bold blue"))
    
    while True:
        e_id = Prompt.ask("請輸入員工 ID (或輸入 'q' 離開)")
        if e_id.lower() in ['q', 'quit', 'exit']:
            sys.exit()
            
        response = client.send_request("login", {"e_id": e_id})
        
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
        console.print("0. 登出 (Logout)")
        
        choice = Prompt.ask("請選擇功能", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "0"])
        
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
        elif choice == "0":
            break

def manage_skills_ui():
    console.print("[bold]管理員工證照[/bold]")
    target_e_id = Prompt.ask("請輸入員工 ID")
    
    console.print("\n[bold]可用證照列表:[/bold]")
    console.print("1. Carnivore (食肉動物)")
    console.print("2. Herbivore (食草動物)")
    console.print("3. Reptile (爬蟲類)")
    console.print("4. Primate (靈長類)")
    console.print("5. Bird (鳥類)")
    console.print("6. Marine (海洋生物)")
    
    choice = Prompt.ask("請選擇證照代號", choices=["1", "2", "3", "4", "5", "6"])
    
    skill_map = {
        "1": "Carnivore",
        "2": "Herbivore",
        "3": "Reptile",
        "4": "Primate",
        "5": "Bird",
        "6": "Marine"
    }
    skill_name = skill_map[choice]
    
    response = client.send_request("add_employee_skill", {
        "target_e_id": target_e_id,
        "skill_name": skill_name
    })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def add_feeding_ui(user_id):
    console.print("[bold]新增餵食紀錄[/bold]")
    a_id = Prompt.ask("請輸入動物 ID")
    
    # [UX] Show recent records
    response = client.send_request("get_recent_records", {"table_name": TABLE_FEEDING, "filter_id": a_id})
    records = response.get("data", [])
    if records:
        r_table = Table(title=f"動物 {a_id} 的最近餵食紀錄")
        r_table.add_column("日期", style="cyan")
        r_table.add_column("飼料", style="yellow")
        r_table.add_column("數量 (kg)", style="green")
        for r in records[:3]: # Show top 3
            r_table.add_row(str(r[1]), r[2], str(r[3]))
        console.print(r_table)
    
    f_id = Prompt.ask("請輸入飼料 ID (例如: F001)")
    
    while True:
        amount = FloatPrompt.ask("請輸入數量 (kg)")
        if amount > 0:
            break
        console.print("[red]數量必須大於 0[/red]")
        
    response = client.send_request("add_feeding", {
        "a_id": a_id, "f_id": f_id, "amount": amount, "user_id": user_id
    })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def add_body_info_ui(user_id):
    console.print("[bold]新增身體資訊[/bold]")
    a_id = Prompt.ask("請輸入動物 ID")
    
    # [UX] Show recent records
    response = client.send_request("get_recent_records", {"table_name": TABLE_ANIMAL_STATE, "filter_id": a_id})
    records = response.get("data", [])
    if records:
        r_table = Table(title=f"動物 {a_id} 的最近體重紀錄")
        r_table.add_column("日期", style="cyan")
        r_table.add_column("體重 (kg)", style="green")
        for r in records[:3]: # Show top 3
            r_table.add_row(str(r[1]), str(r[2]))
        console.print(r_table)
    
    while True:
        weight = FloatPrompt.ask("請輸入體重 (kg)")
        if weight > 0:
            break
        console.print("[red]體重必須大於 0[/red]")
        
    response = client.send_request("add_animal_state", {
        "a_id": a_id, "weight": weight, "user_id": user_id
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
    target_e_id = Prompt.ask("請輸入目標員工 ID")
    t_id = Prompt.ask("請輸入工作 ID")
    
    start_time = Prompt.ask("請輸入開始時間 (YYYY-MM-DD HH:MM:SS)")
    end_time = Prompt.ask("請輸入結束時間 (YYYY-MM-DD HH:MM:SS)")
    
    # Optional a_id
    a_id = Prompt.ask("請輸入負責動物 ID (選填, 若無請直接 Enter)", default="")
    if a_id == "": a_id = None
    
    response = client.send_request("assign_task", {
        "e_id": target_e_id, "t_id": t_id, "start_time": start_time, "end_time": end_time, "a_id": a_id
    })
    
    if response.get("success"):
        console.print(f"[green]{response.get('message')}[/green]")
    else:
        console.print(f"[red]{response.get('message')}[/red]")

def restock_inventory_ui(user_id):
    console.print("[bold]庫存進貨[/bold]")
    f_id = Prompt.ask("請輸入飼料 ID")
    
    while True:
        amount = FloatPrompt.ask("請輸入數量 (kg)")
        if 0 < amount < 100000:
            break
        console.print("[red]數量必須大於 0 且小於 100,000[/red]")
        
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
    
    t_choice = Prompt.ask("選擇", choices=["1", "2"])
    table = table_map[t_choice]
    
    # Step 1: Filter by Animal ID to find records
    a_id = Prompt.ask("請輸入動物 ID 以搜尋紀錄")
    
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
    record_id = Prompt.ask("請輸入要修正的紀錄 ID (參考上表)")
    
    col_choice = ""
    col_name = ""
    
    if table == TABLE_FEEDING:
        console.print("請選擇要修正的欄位:")
        console.print(f"1. {COL_AMOUNT} (餵食量)")
        console.print("2. feed_date (時間 - 不建議手動修改)")
        col_choice = Prompt.ask("選擇", choices=["1"])
        if col_choice == "1": col_name = COL_AMOUNT
        
    elif table == TABLE_ANIMAL_STATE:
        # Only one choice, auto-select
        col_name = COL_WEIGHT

    new_val = FloatPrompt.ask(f"請輸入 {col_name} 的正確數值")
    
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
    a_id = Prompt.ask("請輸入動物 ID")
    
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
    
    choice = Prompt.ask("請選擇資料表", choices=["1", "2", "3", "4"])
    
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
            sys.exit()

if __name__ == "__main__":
    main()
