import socket
import json
import time
import sys

HOST = '127.0.0.1'
PORT = 60000

def send_request(action, data=None):
    if data is None:
        data = {}
    
    request = {
        "action": action,
        "data": data
    }
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(json.dumps(request, default=str).encode('utf-8'))
            response_data = s.recv(16384).decode('utf-8')
            return json.loads(response_data)
    except Exception as e:
        return {"success": False, "message": f"Error: {e}"}

def test():
    print("--- Testing Client-Server Architecture ---")
    
    # 1. Test Login (Assuming employee ID 1 exists from init script)
    print("Testing Login...")
    resp = send_request("login", {"e_id": "1"})
    print(f"Login Response: {resp}")
    
    if resp.get("success"):
        print("[PASS] Login successful.")
    else:
        print("[FAIL] Login failed.")

    # 2. Test Get Reference Data
    print("\nTesting Get Reference Data (Animals)...")
    resp = send_request("get_reference_data", {"table_name": "animal"})
    data = resp.get("data", [])
    print(f"Got {len(data)} animals.")
    if len(data) > 0:
        print("[PASS] Reference data retrieval successful.")
    else:
        print("[FAIL] No data retrieved.")

if __name__ == "__main__":
    # Wait a bit for server to start if run immediately after
    time.sleep(2)
    test()
