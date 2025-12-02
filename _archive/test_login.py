from DB_utils import ZooBackend
import sys

def test_login():
    print("--- Testing Login ---")
    backend = ZooBackend()
    
    # Test Admin Login
    print(f"Attempting login with E001 (Expected: Admin)...")
    result = backend.login("E001")
    print(f"Result: {result}")
    
    # Test User Login
    print(f"Attempting login with E003 (Expected: User)...")
    result = backend.login("E003")
    print(f"Result: {result}")
    
    # Test Invalid Login
    print(f"Attempting login with INVALID (Expected: False)...")
    result = backend.login("INVALID")
    print(f"Result: {result}")

if __name__ == "__main__":
    test_login()
