#!/usr/bin/env python3
"""Read-mostly smoke checks for the local Zoo Management System.

This test intentionally avoids write-heavy business operations such as feeding,
inventory restock, record correction, and employee updates. It is intended as a
quick confidence check before demos or refactors.
"""

import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from DB_utils import ZooBackend
from config import COLLECTION_HEALTH_ALERTS, COLLECTION_LOGIN_LOGS


class SmokeFailure(Exception):
    pass


def check(condition, label, detail=""):
    if not condition:
        raise SmokeFailure(f"{label} failed. {detail}".strip())
    suffix = f" - {detail}" if detail else ""
    print(f"[OK] {label}{suffix}")


def main():
    backend = ZooBackend()
    try:
        check(backend.pg_pool is not None, "PostgreSQL connection pool")
        check(backend.mongo_client is not None, "MongoDB connection")

        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT e_name, role, status, password_hash
                FROM employee
                WHERE e_id = 'E001'
                """
            )
            admin = cur.fetchone()
            check(admin is not None, "Admin account exists")
            check(admin[1] == "Admin", "Admin role", admin[1])
            check(admin[2] == "active", "Admin active status", admin[2])
            check(
                admin[3] == hashlib.sha256("zoo123".encode()).hexdigest(),
                "Demo password hash",
            )

            cur.execute(
                """
                SELECT a.a_id, a.a_name, a.species
                FROM employee_shift s
                JOIN animal a ON a.a_id = s.a_id
                WHERE s.e_id = 'E003'
                  AND now() BETWEEN s.shift_start AND s.shift_end
                ORDER BY a.a_id
                """
            )
            current_animals = cur.fetchall()
            check(
                len(current_animals) > 0,
                "E003 current assignments",
                f"{len(current_animals)} animals; run scripts/refresh_demo_data.py if this fails",
            )

            cur.execute(
                """
                SELECT COUNT(*)
                FROM feeding_inventory
                """
            )
            inventory_rows = cur.fetchone()[0]
            check(inventory_rows > 0, "Inventory history rows", str(inventory_rows))

        inventory = backend.get_inventory_report()
        check(isinstance(inventory, list) and len(inventory) > 0, "Inventory report", f"{len(inventory)} feeds")

        allowed, msg = backend.check_shift_permission("E003", current_animals[0][0])
        check(allowed, "E003 permission check", msg)

        alert_count = backend.mongo_db[COLLECTION_HEALTH_ALERTS].count_documents({})
        check(alert_count >= 0, "Mongo health_alerts readable", f"{alert_count} docs")

        login_log_count = backend.mongo_db[COLLECTION_LOGIN_LOGS].count_documents({})
        check(login_log_count >= 0, "Mongo login_logs readable", f"{login_log_count} docs")

        print("\nSmoke checks passed.")
    finally:
        backend.close()


if __name__ == "__main__":
    try:
        main()
    except SmokeFailure as exc:
        print(f"[FAIL] {exc}")
        sys.exit(1)
