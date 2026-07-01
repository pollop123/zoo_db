#!/usr/bin/env python3
"""Smoke-check the local Zoo Management System data layer."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from DB_utils import ZooBackend


class VerificationError(Exception):
    pass


def check(condition, label, detail=""):
    if not condition:
        raise VerificationError(f"{label} failed. {detail}".strip())
    suffix = f" - {detail}" if detail else ""
    print(f"[OK] {label}{suffix}")


def main():
    backend = ZooBackend()
    try:
        check(backend.pg_pool is not None, "PostgreSQL connection pool")
        check(backend.mongo_client is not None, "MongoDB connection")

        login = backend.login("E001", "zoo123")
        check(login[0], "Admin login", login[3])

        inventory = backend.get_inventory_report()
        check(isinstance(inventory, list) and len(inventory) > 0, "Inventory report", f"{len(inventory)} feeds")

        alerts = backend.get_pending_health_alerts()
        check(isinstance(alerts, list), "Pending health alerts", f"{len(alerts)} alerts")

        careless = backend.get_careless_employees()
        check(isinstance(careless, list), "Careless employee report", f"{len(careless)} employees")

        my_animals = backend.get_my_animals("E003")
        check(
            isinstance(my_animals, list) and len(my_animals) > 0,
            "E003 current animal assignments",
            f"{len(my_animals)} animals; run scripts/refresh_demo_data.py if this fails",
        )

        allowed, msg = backend.check_shift_permission("E003", my_animals[0][0])
        check(allowed, "E003 permission check", msg)

        print("\nSystem verification passed.")
    finally:
        backend.close()


if __name__ == "__main__":
    try:
        main()
    except VerificationError as exc:
        print(f"[FAIL] {exc}")
        sys.exit(1)
