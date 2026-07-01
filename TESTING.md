# Testing Guide

This project has three testing levels. They are separated because some checks are read-only, while others intentionally mutate demo data.

## 1. Smoke Checks

Use this before demos, before refactors, and after pulling changes:

```bash
python scripts/refresh_demo_data.py
python test/test_smoke.py
```

`test/test_smoke.py` checks database connectivity, core demo accounts, current E003 assignments, inventory readability, permission checks, and MongoDB collection readability. It avoids write-heavy business operations.

## 2. System Verification

Use this when you want a higher-level application check:

```bash
python scripts/verify_system.py
```

This uses `ZooBackend` application methods and verifies the same flow that the server depends on. It calls the login method, so it may add a MongoDB login log entry.

## 3. Integration and Demo Tests

Use these when you intentionally want to exercise write paths:

```bash
python test/test_agent.py
python test/test_lock_demo.py
```

`test/test_agent.py` runs broad feature checks and can insert or update data such as feeding records, body records, employee status, skills, diet settings, and audit/careless records.

`test/test_lock_demo.py` demonstrates concurrent feeding and PostgreSQL locking. It intentionally writes inventory and feeding rows, then attempts to restore PostgreSQL from `zoo.backup` unless `--no-restore` is passed.

## Recommended Order

```bash
python scripts/refresh_demo_data.py
python test/test_smoke.py
python scripts/verify_system.py
```

Run the integration/demo tests only when database mutation is acceptable.
