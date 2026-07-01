#!/usr/bin/env python3
"""Refresh deterministic demo shifts for the next few days."""

import os
import sys
from datetime import date, datetime, time, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from DB_utils import ZooBackend


DEMO_SHIFTS = [
    ("E003", "T006", "A002"),  # Carnivore user demo: Lion
    ("E003", "T006", "A003"),  # Penguin user demo
    ("E004", "T005", "A004"),  # Endangered user demo: Koala
    ("E002", "T006", "A003"),  # Valid Penguin assignment
]

NEGATIVE_PERMISSION_CASE = ("E002", "T006", "A002")


def ensure_entities(cur):
    employee_ids = {shift[0] for shift in DEMO_SHIFTS}
    employee_ids.add(NEGATIVE_PERMISSION_CASE[0])
    task_ids = {shift[1] for shift in DEMO_SHIFTS}
    task_ids.add(NEGATIVE_PERMISSION_CASE[1])
    animal_ids = {shift[2] for shift in DEMO_SHIFTS}
    animal_ids.add(NEGATIVE_PERMISSION_CASE[2])

    cur.execute("SELECT e_id FROM employee WHERE e_id = ANY(%s)", (list(employee_ids),))
    found_employees = {row[0] for row in cur.fetchall()}
    missing_employees = sorted(employee_ids - found_employees)

    cur.execute("SELECT t_id FROM task WHERE t_id = ANY(%s)", (list(task_ids),))
    found_tasks = {row[0] for row in cur.fetchall()}
    missing_tasks = sorted(task_ids - found_tasks)

    cur.execute("SELECT a_id FROM animal WHERE a_id = ANY(%s)", (list(animal_ids),))
    found_animals = {row[0] for row in cur.fetchall()}
    missing_animals = sorted(animal_ids - found_animals)

    missing = []
    if missing_employees:
        missing.append(f"employees={missing_employees}")
    if missing_tasks:
        missing.append(f"tasks={missing_tasks}")
    if missing_animals:
        missing.append(f"animals={missing_animals}")
    if missing:
        raise RuntimeError("Missing required demo entities: " + "; ".join(missing))


def refresh_demo_shifts(days=7):
    backend = ZooBackend()
    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            ensure_entities(cur)

            demo_employees = sorted({shift[0] for shift in DEMO_SHIFTS} | {NEGATIVE_PERMISSION_CASE[0]})
            start_day = date.today()
            end_day = start_day + timedelta(days=days - 1)

            cur.execute(
                """
                DELETE FROM employee_shift
                WHERE shift_id LIKE 'DMO%%'
                   OR (
                        e_id = ANY(%s)
                    AND shift_start::date BETWEEN %s AND %s
                   )
                """,
                (demo_employees, start_day, end_day),
            )

            inserted = 0
            for offset in range(days):
                current_day = start_day + timedelta(days=offset)
                shift_start = datetime.combine(current_day, time(0, 0, 0))
                shift_end = datetime.combine(current_day, time(23, 59, 59))

                for index, (e_id, t_id, a_id) in enumerate(DEMO_SHIFTS, 1):
                    shift_id = f"DMO{current_day:%y%m%d}{index:02d}"
                    cur.execute(
                        """
                        INSERT INTO employee_shift (shift_id, e_id, t_id, shift_start, shift_end, a_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (shift_id, e_id, t_id, shift_start, shift_end, a_id),
                    )
                    inserted += 1

            conn.commit()
            return inserted, start_day, end_day
    finally:
        backend.close()


def main():
    inserted, start_day, end_day = refresh_demo_shifts()
    print(f"Refreshed {inserted} demo shifts from {start_day} to {end_day}.")
    print("Demo users with current assignments: E003, E004, E002.")
    print("Permission-negative scenario remains: E002 lacks Carnivore for A002.")


if __name__ == "__main__":
    main()
