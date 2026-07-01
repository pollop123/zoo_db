"""Read-only reference and report queries for ZooBackend."""

from config import *


def get_all_tasks(backend):
    """查詢所有工作類型"""
    if not backend.pg_pool:
        return []

    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT t_id, t_name
                FROM {TABLE_TASK}
                ORDER BY t_id
            """)
            rows = cur.fetchall()
            return [{"t_id": r[0], "t_name": r[1]} for r in rows]
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []


def get_all_animals(backend):
    """查詢所有動物"""
    if not backend.pg_pool:
        return []

    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT a.a_id, a.a_name, a.species, s.required_skill
                FROM {TABLE_ANIMAL} a
                JOIN {TABLE_SPECIES} s ON a.species = s.s_name
                ORDER BY a.a_id
            """)
            rows = cur.fetchall()
            return [{"a_id": r[0], "a_name": r[1], "species": r[2], "required_skill": r[3]} for r in rows]
    except Exception as e:
        print(f"Error fetching animals: {e}")
        return []


def get_animal_diet(backend, species):
    """查詢某物種可食用的飼料"""
    if not backend.pg_pool:
        return []

    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT d.f_id, f.feed_name, f.category
                FROM animal_diet d
                JOIN feeds f ON d.f_id = f.f_id
                WHERE d.species = %s
                ORDER BY f.category, f.f_id
            """, (species,))
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching animal diet: {e}")
        return []


def get_all_diet_settings(backend):
    """查詢所有物種的飲食設定"""
    if not backend.pg_pool:
        return []

    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT d.species, d.f_id, f.feed_name, f.category
                FROM animal_diet d
                JOIN feeds f ON d.f_id = f.f_id
                ORDER BY d.species, f.category, f.f_id
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching diet settings: {e}")
        return []


def get_all_species(backend):
    """取得所有物種列表"""
    if not backend.pg_pool:
        return []

    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT s_name FROM {TABLE_SPECIES} ORDER BY s_name")
            return [r[0] for r in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching species: {e}")
        return []


def get_all_feeds(backend):
    """取得所有飼料列表"""
    if not backend.pg_pool:
        return []

    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT f_id, feed_name, category FROM feeds ORDER BY category, f_id")
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching feeds: {e}")
        return []


def get_inventory_report(backend):
    """庫存報表"""
    if not backend.pg_pool:
        return []

    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT
                    f.f_id,
                    f.feed_name,
                    COALESCE(SUM(i.quantity_delta_kg), 0) as current_stock
                FROM {TABLE_FEEDS} f
                LEFT JOIN {TABLE_INVENTORY} i ON i.f_id = f.f_id
                GROUP BY f.f_id, f.feed_name
                ORDER BY current_stock ASC
            """)
            results = []
            for row in cur.fetchall():
                results.append({
                    "f_id": row[0],
                    "f_name": row[1],
                    "unit": "kg",
                    "current_stock": float(row[2]) if row[2] else 0
                })
            return results
    except Exception as e:
        print(f"Error fetching inventory report: {e}")
        return []


def get_animal_trends(backend, a_id):
    """動物趨勢 (體重與餵食)"""
    if not backend.pg_pool:
        return {}, {}

    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT datetime, {COL_WEIGHT}
                FROM {TABLE_ANIMAL_STATE}
                WHERE a_id = %s
                ORDER BY datetime DESC
                LIMIT 5
            """, (a_id,))
            weights = cur.fetchall()

            cur.execute(f"""
                SELECT feed_date, f.feed_name, r.{COL_AMOUNT}
                FROM {TABLE_FEEDING} r
                JOIN {TABLE_FEEDS} f ON r.f_id = f.f_id
                WHERE r.a_id = %s
                ORDER BY feed_date DESC
                LIMIT 5
            """, (a_id,))
            feedings = cur.fetchall()

            return weights, feedings
    except Exception as e:
        print(f"Error fetching trends: {e}")
        return {}, {}


def get_reference_data(backend, table_name):
    """查詢代碼表 (Reference Lookup)"""
    if not backend.pg_pool:
        return []

    queries = {
        "animal": f"SELECT a_id, a_name, species FROM {TABLE_ANIMAL} ORDER BY a_id",
        "feeds": f"SELECT f_id, feed_name, category FROM {TABLE_FEEDS} ORDER BY f_id",
        "task": f"SELECT t_id, t_name FROM {TABLE_TASK} ORDER BY t_id",
        "employee": f"SELECT e_id, e_name, role FROM {TABLE_EMPLOYEES} ORDER BY e_id",
        "status_type": f"SELECT s_id, s_name, description FROM {TABLE_STATUS_TYPE} ORDER BY s_id",
    }
    query = queries.get(table_name)
    if not query:
        return []

    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(query)
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching reference data: {e}")
        return []


def get_recent_records(backend, table_name, filter_id):
    """取得最近的紀錄，輔助修正功能"""
    if not backend.pg_pool:
        return []

    if table_name == TABLE_FEEDING:
        query = f"""
            SELECT r.{COL_FEEDING_ID}, r.feed_date, f.feed_name, r.{COL_AMOUNT}
            FROM {TABLE_FEEDING} r
            JOIN {TABLE_FEEDS} f ON r.f_id = f.f_id
            WHERE r.a_id = %s
            ORDER BY r.feed_date DESC
            LIMIT 10
        """
    elif table_name == TABLE_ANIMAL_STATE:
        query = f"""
            SELECT record_id, datetime, {COL_WEIGHT}
            FROM {TABLE_ANIMAL_STATE}
            WHERE a_id = %s
            ORDER BY datetime DESC
            LIMIT 10
        """
    else:
        return []

    try:
        with backend.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (filter_id,))
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching recent records: {e}")
        return []
