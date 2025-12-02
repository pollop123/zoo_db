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
    "add_animal_state": AddAnimalStateAction
}

class ClientHandler(threading.Thread):
    def __init__(self, conn, addr, db_backend):
        super().__init__()
        self.conn = conn
        self.addr = addr
        self.db_backend = db_backend

    def run(self):
        print(f"[NEW CONNECTION] {self.addr} connected.")
        try:
            while True:
                # Receive data
                data = self.conn.recv(4096).decode('utf-8')
                if not data:
                    break
                
                try:
                    request = json.loads(data)
                    action_name = request.get('action')
                    params = request.get('data', {})
                    
                    print(f"[{self.addr}] Request Action: {action_name}")
                    
                    if action_name in ACTION_MAP:
                        action_cls = ACTION_MAP[action_name]
                        action_instance = action_cls()
                        
                        # Execute Action
                        # Note: In a real app, we should check permissions here using Role
                        # But for now, we trust the client or the action to handle it.
                        # The DB_utils is shared, so we rely on its internal handling.
                        # For strictly correct threading with transactions, we might need a lock
                        # or separate DB instances. For this project, we'll share.
                        response = action_instance.execute(self.db_backend, **params)
                    else:
                        response = {"success": False, "message": f"Unknown action: {action_name}"}
                    
                    # Send response
                    self.conn.sendall(json.dumps(response, default=str).encode('utf-8'))
                    
                except json.JSONDecodeError:
                    print(f"[{self.addr}] Invalid JSON received.")
                    error_resp = {"success": False, "message": "Invalid JSON format"}
                    self.conn.sendall(json.dumps(error_resp).encode('utf-8'))
                except Exception as e:
                    print(f"[{self.addr}] Error processing request: {e}")
                    traceback.print_exc()
                    error_resp = {"success": False, "message": f"Server Error: {str(e)}"}
                    self.conn.sendall(json.dumps(error_resp).encode('utf-8'))

        except Exception as e:
            print(f"[{self.addr}] Connection error: {e}")
        finally:
            print(f"[DISCONNECTED] {self.addr} disconnected.")
            self.conn.close()

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
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("[STOPPING] Server is stopping...")
    finally:
        db_backend.close()
        server.close()

if __name__ == "__main__":
    start_server()
