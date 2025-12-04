import socket
import threading
import json
import traceback
from DB_utils import ZooBackend

# Import Actions
from action.auth import LoginAction, LogoutAction
from action.feeding import AddFeedingAction
from action.inventory import AddInventoryStockAction, GetInventoryReportAction
from action.schedule import GetEmployeeScheduleAction, AssignTaskAction
from action.record import CorrectRecordAction, GetRecentRecordsAction
from action.analysis import (
    CheckWeightAnomalyAction, BatchCheckAnomaliesAction, 
    GetHighRiskAnimalsAction, GetAnimalTrendsAction, GetAuditLogsAction,
    GetCarelessEmployeesAction
)
from action.reference import GetReferenceDataAction
from action.body_info import AddAnimalStateAction
from action.skill import AddEmployeeSkillAction

# Configuration
HOST = '127.0.0.1'
PORT = 60000

# Action Mapping
ACTION_MAP = {
    "login": LoginAction,
    "logout": LogoutAction,
    "add_feeding": AddFeedingAction,
    "add_inventory_stock": AddInventoryStockAction,
    "get_inventory_report": GetInventoryReportAction,
    "get_employee_schedule": GetEmployeeScheduleAction,
    "assign_task": AssignTaskAction,
    "correct_record": CorrectRecordAction,
    "get_recent_records": GetRecentRecordsAction,
    "check_weight_anomaly": CheckWeightAnomalyAction,
    "batch_check_anomalies": BatchCheckAnomaliesAction,
    "get_high_risk_animals": GetHighRiskAnimalsAction,
    "get_animal_trends": GetAnimalTrendsAction,
    "get_audit_logs": GetAuditLogsAction,
    "get_careless_employees": GetCarelessEmployeesAction,
    "get_reference_data": GetReferenceDataAction,
    "add_animal_state": AddAnimalStateAction,
    "add_employee_skill": AddEmployeeSkillAction
}

class ClientHandler(threading.Thread):
    def __init__(self, conn, addr, db_backend):
        super().__init__()
        self.conn = conn
        self.addr = addr
        self.db_backend = db_backend

    def _format_params(self, action_name, params):
        """格式化參數摘要用於日誌"""
        if action_name == "login":
            return params.get("e_id", "-")
        elif action_name == "add_feeding":
            return f"{params.get('a_id')}, {params.get('f_id')}, {params.get('amount')}kg"
        elif action_name == "add_animal_state":
            return f"{params.get('a_id')}, {params.get('weight')}kg"
        elif action_name == "add_inventory_stock":
            return f"{params.get('f_id')}, +{params.get('amount')}kg"
        elif action_name == "assign_task":
            return f"{params.get('e_id')} -> {params.get('t_id')}, {params.get('a_id') or '無指定動物'}"
        elif action_name == "correct_record":
            return f"{params.get('table')}, ID:{params.get('record_id')}"
        elif action_name == "add_employee_skill":
            return f"{params.get('target_e_id')} <- {params.get('skill_name')}"
        elif action_name == "get_animal_trends":
            return params.get("a_id", "-")
        elif action_name == "get_reference_data":
            return params.get("table_name", "-")
        else:
            return "-"

    def run(self):
        print(f"[CONNECTED] {self.addr}")
        buffer = ""
        try:
            while True:
                # Receive data
                chunk = self.conn.recv(4096).decode('utf-8')
                if not chunk:
                    break
                
                buffer += chunk
                
                # 處理所有完整的訊息（以換行符分隔）
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    if not message.strip():
                        continue
                    
                    try:
                        request = json.loads(message)
                        action_name = request.get('action')
                        params = request.get('data', {})
                        
                        # 取得操作者 ID
                        user_id = params.get('user_id') or params.get('e_id') or '-'
                        
                        # 格式化參數摘要
                        param_summary = self._format_params(action_name, params)
                        
                        if action_name in ACTION_MAP:
                            action_cls = ACTION_MAP[action_name]
                            action_instance = action_cls()
                            response = action_instance.execute(self.db_backend, **params)
                            
                            # 格式化結果
                            status = "成功" if response.get("success") else "失敗"
                            msg = response.get("message", "")[:50]  # 截斷過長訊息
                            
                            print(f"[{user_id}] {action_name} -> {param_summary} -> {status}: {msg}")
                        else:
                            response = {"success": False, "message": f"Unknown action: {action_name}"}
                            print(f"[{user_id}] {action_name} -> 未知操作")
                        
                        # Send response (加換行符作為訊息結尾)
                        response_json = json.dumps(response, default=str) + "\n"
                        self.conn.sendall(response_json.encode('utf-8'))
                        
                    except json.JSONDecodeError:
                        print(f"[{self.addr}] Invalid JSON received.")
                        error_resp = {"success": False, "message": "Invalid JSON format"}
                        self.conn.sendall((json.dumps(error_resp) + "\n").encode('utf-8'))
                    except Exception as e:
                        print(f"[{self.addr}] Error processing request: {e}")
                        traceback.print_exc()
                        error_resp = {"success": False, "message": f"Server Error: {str(e)}"}
                        self.conn.sendall((json.dumps(error_resp) + "\n").encode('utf-8'))

        except Exception as e:
            print(f"[{self.addr}] Connection error: {e}")
        finally:
            self.conn.close()
            print(f"[OFFLINE] {self.addr} 離線，目前上線人數: {threading.active_count() - 2}")


def start_server():
    print("[STARTING] Server is starting...")
    # Initialize Database Connection
    db_backend = ZooBackend()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            thread = ClientHandler(conn, addr, db_backend)
            thread.start()
            print(f"[ONLINE] 目前上線人數: {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("[STOPPING] Server is stopping...")
    finally:
        db_backend.close()
        server.close()

if __name__ == "__main__":
    start_server()
