# DB_utils.py Split Plan

`DB_utils.py` currently works as the central application service: it owns database connections, business rules, SQL queries, MongoDB audit behavior, anomaly detection, and transaction-heavy workflows. That is acceptable for the current course project, but future changes will be easier if the file is split gradually.

## Current Responsibility Groups

| Area | Examples | Risk |
|------|----------|------|
| Connection management | PostgreSQL pool, MongoDB client, `get_db_connection` | Low |
| Auth and employees | login, password lookup/change, employee CRUD, skills | Medium |
| Schedule and permissions | schedule lookup, current animals, `check_shift_permission` | Medium |
| Feeding and inventory | `add_feeding_record`, stock report, restock, transaction locks | High |
| Records and correction | recent records, corrections, audit/careless logs | High |
| Anomaly and health | weight/feeding anomaly checks, health alerts | Medium |
| Reference data | animals, feeds, species, tasks, status types | Low |

## Safe Split Order

### Step 1: Extract Read-Only Helpers

Start with low-risk read-only query helpers:

```text
services/reference_service.py
services/report_service.py
```

Move methods such as `get_reference_data`, `get_all_species`, `get_all_feeds`, `get_all_tasks`, and read-only report queries first. Keep `ZooBackend` as the public facade and delegate to the new modules.

Prepared first slice:

```text
services/reference_service.py
```

This first slice keeps all existing `ZooBackend` method names and delegates read-only reference/report methods to the service module. It does not move transaction-heavy feeding logic, permission checks, employee updates, or MongoDB write paths.

### Step 2: Extract MongoDB Event Helpers

Create a small helper for MongoDB serialization and event writes:

```text
services/audit_service.py
```

Keep the original behavior, but centralize insert/find logic for `audit_logs`, `health_alerts`, `careless_logs`, and `login_logs`.

### Step 3: Extract Auth and Employee Logic

Move login/password and employee-management methods after smoke checks are stable:

```text
services/auth_service.py
services/employee_service.py
```

Do not change the demo password behavior during this split; it is a separate product/security decision.

### Step 4: Extract Schedule and Permission Logic

Move schedule lookup and `check_shift_permission` into:

```text
services/schedule_service.py
```

This should happen before touching feeding logic because feeding depends on permission checks.

### Step 5: Extract Feeding and Inventory Last

Leave `add_feeding_record` until last. It contains the highest-risk consistency logic:

```text
services/feeding_service.py
services/inventory_service.py
```

Preserve the existing PostgreSQL transaction boundary, `FOR UPDATE`, and table lock behavior. Do not split the transaction across service calls that each open their own connection.

## Guardrails

- Keep `ZooBackend` as a compatibility facade until all callers are migrated.
- Move code in small commits and run smoke checks after each move.
- Do not change SQL behavior while moving methods.
- Do not split PostgreSQL transaction boundaries during refactors.
- Treat MongoDB audit writes as supporting records; PostgreSQL remains the source of truth for core operational data.

## Minimum Verification After Each Step

```bash
python scripts/refresh_demo_data.py
python test/test_smoke.py
python scripts/verify_system.py
```
