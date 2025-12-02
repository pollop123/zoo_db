import sys
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, FloatPrompt, IntPrompt
from rich.panel import Panel
from rich.layout import Layout
from rich import print as rprint
from backend import ZooBackend
from config import *

console = Console()
backend = ZooBackend()

def login_screen():
    console.clear()
    console.print(Panel.fit("Zoo Management System", style="bold blue"))
    
    while True:
        e_id = Prompt.ask("Enter Employee ID (or 'q' to quit)")
        if e_id.lower() in ['q', 'quit', 'exit']:
            sys.exit()
            
        success, name, role = backend.login(e_id)
        if success:
            console.print(f"[green]Welcome, {name} ({role})![/green]")
            return e_id, name, role
        else:
            console.print("[red]Login failed. Invalid ID or inactive status.[/red]")

def show_user_menu(user_id, name):
    while True:
        console.print("\n[bold cyan]User Menu[/bold cyan]")
        console.print("1. [新增餵食] Add Feeding Record")
        console.print("2. [新增身體資訊] Add Body Info (Weight)")
        console.print("3. [查詢班表] View Schedule")
        console.print("4. [查詢代碼表] View Reference Data (Animals, Feeds, etc.)")
        console.print("5. [修正自己紀錄] Correct My Record")
        console.print("6. [查詢個別動物趨勢] View Animal Trends")
        console.print("0. Logout")
        
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6", "0"])
        
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
        console.print("\n[bold magenta]Admin Menu[/bold magenta]")
        console.print("1. [修正紀錄稽核] View Audit Logs")
        console.print("2. [異常警示] Check/View Weight Anomalies (Single)")
        console.print("3. [批量異常掃描] Batch Anomaly Scan (All Animals)")
        console.print("4. [庫存報表] View Inventory Report")
        console.print("5. [庫存進貨] Restock Inventory")
        console.print("6. [指派工作] Assign Task/Shift")
        console.print("7. [修正紀錄] Correct Record (Admin Override)")
        console.print("8. [高風險動物] View High Risk Animals")
        console.print("9. [查詢個別動物趨勢] View Animal Trends")
        console.print("10. [查詢代碼表] View Reference Data")
        console.print("0. Logout")
        
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "0"])
        
        if choice == "1":
            view_audit_logs_ui()
        elif choice == "2":
            check_anomalies_ui()
        elif choice == "3":
            batch_check_anomalies_ui()
        elif choice == "4":
            view_inventory_report_ui()
        elif choice == "5":
            restock_inventory_ui(user_id)
        elif choice == "6":
            assign_task_ui(user_id)
        elif choice == "7":
            correct_record_ui(user_id)
        elif choice == "8":
            view_high_risk_animals_ui()
        elif choice == "9":
            view_animal_trends_ui()
        elif choice == "10":
            view_reference_data_ui()
        elif choice == "0":
            break

def add_feeding_ui(user_id):
    console.print("[bold]Add Feeding Record[/bold]")
    a_id = IntPrompt.ask("Enter Animal ID")
    f_id = IntPrompt.ask("Enter Food ID (e.g., 1 for Hay, 2 for Fruit)") # Simplified for UI
    
    while True:
        amount = FloatPrompt.ask("Enter Amount (kg)")
        if amount > 0:
            break
        console.print("[red]Amount must be greater than 0.[/red]")
        
    success, msg = backend.add_feeding(a_id, f_id, amount, user_id)
    if success:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]{msg}[/red]")

def add_body_info_ui(user_id):
    console.print("[bold]Add Body Info[/bold]")
    a_id = IntPrompt.ask("Enter Animal ID")
    
    while True:
        weight = FloatPrompt.ask("Enter Weight (kg)")
        if weight > 0:
            break
        console.print("[red]Weight must be greater than 0.[/red]")
        
    success, msg = backend.add_animal_state(a_id, weight, user_id)
    if success:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]{msg}[/red]")

def view_schedule_ui(user_id):
    console.print("[bold]My Schedule[/bold]")
    schedule = backend.get_employee_schedule(user_id)
    
    if not schedule:
        console.print("[yellow]No upcoming shifts found.[/yellow]")
        return

    table = Table(title="My Schedule")
    table.add_column("Start Time", style="cyan")
    table.add_column("End Time", style="cyan")
    table.add_column("Task", style="green")

    for row in schedule:
        table.add_row(str(row[0]), str(row[1]), row[2])
    
    console.print(table)

def assign_task_ui(user_id):
    console.print("[bold]Assign Task / Shift[/bold]")
    target_e_id = IntPrompt.ask("Enter Target Employee ID")
    t_id = IntPrompt.ask("Enter Task ID")
    
    start_time = Prompt.ask("Enter Start Time (YYYY-MM-DD HH:MM:SS)")
    end_time = Prompt.ask("Enter End Time (YYYY-MM-DD HH:MM:SS)")
    
    success, msg = backend.assign_task(target_e_id, t_id, start_time, end_time)
    if success:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]{msg}[/red]")

def restock_inventory_ui(user_id):
    console.print("[bold]Restock Inventory[/bold]")
    f_id = IntPrompt.ask("Enter Food ID")
    
    while True:
        amount = FloatPrompt.ask("Enter Amount (kg)")
        if 0 < amount < 100000: # Limit to prevent overflow
            break
        console.print("[red]Amount must be greater than 0 and less than 100,000.[/red]")
        
    success, msg = backend.add_inventory_stock(f_id, amount, user_id)
    if success:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]{msg}[/red]")

def correct_record_ui(user_id):
    console.print("[bold]Correct Record[/bold]")
    
    # Improved UX: Ask for Animal ID first to show records
    table_map = {
        "1": TABLE_FEEDING,
        "2": TABLE_ANIMAL_STATE
    }
    console.print("Select Table:")
    console.print(f"1. {TABLE_FEEDING} (Feeding Records)")
    console.print(f"2. {TABLE_ANIMAL_STATE} (Animal State)")
    
    t_choice = Prompt.ask("Choice", choices=["1", "2"])
    table = table_map[t_choice]
    
    # Step 1: Filter by Animal ID to find records
    a_id = IntPrompt.ask("Enter Animal ID to find records")
    records = backend.get_recent_records(table, a_id)
    
    if not records:
        console.print("[yellow]No recent records found for this animal.[/yellow]")
        return

    # Display Records
    r_table = Table(title=f"Recent Records for Animal {a_id}")
    r_table.add_column("Record ID", style="cyan")
    r_table.add_column("Date", style="blue")
    
    if table == TABLE_FEEDING:
        r_table.add_column("Feed", style="yellow")
        r_table.add_column("Amount", style="green")
        for r in records:
            r_table.add_row(str(r[0]), str(r[1]), r[2], str(r[3]))
    else:
        r_table.add_column("Weight", style="green")
        for r in records:
            r_table.add_row(str(r[0]), str(r[1]), str(r[2]))
            
    console.print(r_table)
    
    # Step 2: Select Record ID
    record_id = IntPrompt.ask("Enter Record ID to Correct (from above)")
    
    # Improved Column Selection
    col_choice = ""
    col_name = ""
    
    if table == TABLE_FEEDING:
        console.print("Select Column to Fix:")
        console.print(f"1. {COL_AMOUNT} (Feeding Amount)")
        console.print("2. feed_date (Time - Not recommended to change manually)")
        col_choice = Prompt.ask("Choice", choices=["1"]) # Restrict to amount for now for safety
        if col_choice == "1": col_name = COL_AMOUNT
        
    elif table == TABLE_ANIMAL_STATE:
        console.print("Select Column to Fix:")
        console.print(f"1. {COL_WEIGHT} (Weight)")
        col_choice = Prompt.ask("Choice", choices=["1"])
        if col_choice == "1": col_name = COL_WEIGHT

    new_val = FloatPrompt.ask(f"Enter New Correct Value for {col_name}")
    
    success, msg = backend.correct_record(user_id, table, record_id, col_name, new_val)
    if success:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]{msg}[/red]")

def view_audit_logs_ui():
    logs = backend.get_audit_logs()
    if not logs:
        console.print("[yellow]No audit logs found.[/yellow]")
        return

    table = Table(title="Audit Logs (NoSQL)")
    table.add_column("Time", style="cyan")
    table.add_column("Operator", style="magenta")
    table.add_column("Table", style="green")
    table.add_column("Change", style="white")

    for log in logs:
        change_str = f"{log['change']['field']}: {log['change']['old_value']} -> {log['change']['new_value']}"
        table.add_row(log['timestamp'], str(log['operator_id']), log['target_table'], change_str)
    
    console.print(table)

def check_anomalies_ui():
    console.print("[bold]Weight Anomaly Check[/bold]")
    a_id = IntPrompt.ask("Enter Animal ID to Check")
    
    success, msg, pct = backend.check_weight_anomaly(a_id)
    if success:
        console.print(f"[red]{msg}[/red]")
        console.print("[bold red]Alert saved to NoSQL.[/bold red]")
    else:
        console.print(f"[green]{msg}[/green]")

def batch_check_anomalies_ui():
    console.print("[bold]Batch Anomaly Scan[/bold]")
    console.print("Scanning all animals... please wait.")
    
    anomalies = backend.batch_check_anomalies()
    
    if not anomalies:
        console.print("[green]Scan complete. No anomalies found.[/green]")
        return

    console.print(f"[red]Scan complete. Found {len(anomalies)} anomalies![/red]")
    
    table = Table(title="Detected Anomalies")
    table.add_column("Animal ID", style="cyan")
    table.add_column("Name", style="yellow")
    table.add_column("Change %", style="red")
    table.add_column("Message", style="white")
    
    for a in anomalies:
        table.add_row(str(a['id']), a['name'], f"{a['pct']:.1f}%", a['msg'])
        
    console.print(table)
    console.print("[bold red]All alerts have been saved to NoSQL.[/bold red]")

def view_high_risk_animals_ui():
    results = backend.get_high_risk_animals()
    if not results:
        console.print("[green]No high risk animals found (Anomalies < 3).[/green]")
        return

    table = Table(title="High Risk Animals (>= 3 Anomalies)")
    table.add_column("Animal ID", style="red")
    table.add_column("Anomaly Count", style="yellow")

    for res in results:
        table.add_row(str(res['_id']), str(res['count']))
    
    console.print(table)

def view_inventory_report_ui():
    data = backend.get_inventory_report()
    if not data:
        console.print("[yellow]No inventory data found.[/yellow]")
        return

    table = Table(title="Inventory Report")
    table.add_column("Feed Name", style="cyan")
    table.add_column("Current Stock (kg)", style="green")

    for row in data:
        table.add_row(row[0], str(row[1]))
    
    console.print(table)

def view_animal_trends_ui():
    console.print("[bold]View Animal Trends[/bold]")
    a_id = IntPrompt.ask("Enter Animal ID")
    
    weights, feedings = backend.get_animal_trends(a_id)
    
    if weights:
        w_table = Table(title=f"Recent Weights (Animal {a_id})")
        w_table.add_column("Date", style="cyan")
        w_table.add_column("Weight (kg)", style="green")
        for w in weights:
            w_table.add_row(str(w[0]), str(w[1]))
        console.print(w_table)
    else:
        console.print("[yellow]No weight records found.[/yellow]")

    if feedings:
        f_table = Table(title=f"Recent Feedings (Animal {a_id})")
        f_table.add_column("Date", style="cyan")
        f_table.add_column("Feed", style="yellow")
        f_table.add_column("Amount (kg)", style="white")
        for f in feedings:
            f_table.add_row(str(f[0]), f[1], str(f[2]))
        console.print(f_table)
    else:
        console.print("[yellow]No feeding records found.[/yellow]")

def view_reference_data_ui():
    console.print("[bold]View Reference Data[/bold]")
    console.print("1. Animals")
    console.print("2. Feeds")
    console.print("3. Tasks")
    console.print("4. Employees")
    
    choice = Prompt.ask("Select Table", choices=["1", "2", "3", "4"])
    
    table_name = ""
    title = ""
    if choice == "1": 
        table_name = "animal"
        title = "Animal List"
    elif choice == "2": 
        table_name = "feeds"
        title = "Feed List"
    elif choice == "3": 
        table_name = "task"
        title = "Task List"
    elif choice == "4":
        table_name = "employee"
        title = "Employee List"
        
    data = backend.get_reference_data(table_name)
    
    if not data:
        console.print("[yellow]No data found.[/yellow]")
        return

    table = Table(title=title)
    if choice == "1":
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Species", style="yellow")
        for row in data:
            table.add_row(str(row[0]), row[1], row[2])
    elif choice == "2":
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Category", style="yellow")
        for row in data:
            table.add_row(str(row[0]), row[1], row[2])
    elif choice == "3":
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        for row in data:
            table.add_row(str(row[0]), row[1])
    elif choice == "4":
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Role", style="magenta")
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
            console.print("\n[bold]Goodbye![/bold]")
            sys.exit()

if __name__ == "__main__":
    main()
