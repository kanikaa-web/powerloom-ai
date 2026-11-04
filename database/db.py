"""
db.py
-----
SQLite database layer for the Powerloom Smart Prediction System.
Handles schema creation and CRUD helper functions for:
users, stock, stock_history, orders, suppliers, predictions_log.
"""

import sqlite3
import os
import logging
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "powerloom.db")


@contextmanager
def get_connection():
    """Context manager for safe DB connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they do not exist."""
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Admin','Manager','Employee')),
            full_name TEXT,
            email TEXT,
            security_question TEXT,
            security_answer_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_name TEXT UNIQUE NOT NULL,
            current_stock REAL NOT NULL DEFAULT 0,
            safety_stock REAL NOT NULL DEFAULT 0,
            reorder_level REAL NOT NULL DEFAULT 0,
            unit TEXT DEFAULT 'kg',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_name TEXT NOT NULL,
            change_qty REAL NOT NULL,
            change_type TEXT CHECK(change_type IN ('IN','OUT')),
            note TEXT,
            performed_by TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            material_supplied TEXT,
            price_per_unit REAL,
            quality_rating REAL,
            avg_delivery_days REAL,
            rating REAL,
            availability TEXT DEFAULT 'Available'
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            customer TEXT,
            fabric_type TEXT,
            quantity REAL,
            delivery_date TEXT,
            priority TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT,
            input_json TEXT,
            output_json TEXT,
            performed_by TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_type TEXT,
            service_date TEXT,
            work_done TEXT,
            downtime_hours REAL,
            cost REAL,
            performed_by TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        conn.commit()
        logger.info("Database initialized successfully.")


def seed_default_data():
    """Insert default admin user, sample stock, and suppliers if empty."""
    from utils.auth import hash_password

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) as c FROM users")
        if cur.fetchone()["c"] == 0:
            defaults = [
                ("admin", hash_password("Admin@123"), "Admin", "System Administrator", "admin@powerloom.com"),
                ("manager", hash_password("Manager@123"), "Manager", "Production Manager", "manager@powerloom.com"),
                ("employee", hash_password("Employee@123"), "Employee", "Floor Employee", "employee@powerloom.com"),
            ]
            cur.executemany(
                "INSERT INTO users (username, password_hash, role, full_name, email) VALUES (?,?,?,?,?)",
                defaults
            )
            logger.info("Default users created (admin/manager/employee).")

        cur.execute("SELECT COUNT(*) as c FROM stock")
        if cur.fetchone()["c"] == 0:
            materials = [
                ("Cotton", 4500, 800, 1040, "kg"),
                ("Yarn", 3600, 600, 780, "kg"),
                ("Polyester", 2700, 500, 650, "kg"),
                ("Dye", 700, 150, 195, "litre"),
                ("Chemical", 450, 100, 130, "litre"),
                ("Packing Material", 1100, 200, 260, "units"),
            ]
            cur.executemany(
                "INSERT INTO stock (material_name, current_stock, safety_stock, reorder_level, unit) VALUES (?,?,?,?,?)",
                materials
            )

        cur.execute("SELECT COUNT(*) as c FROM suppliers")
        if cur.fetchone()["c"] == 0:
            suppliers = [
                ("ShreeTex Suppliers", "Cotton", 165, 4.5, 4, 4.6, "Available"),
                ("Om Sai Yarns", "Yarn", 210, 4.2, 5, 4.3, "Available"),
                ("Balaji Cotton Mills", "Cotton", 158, 4.0, 6, 4.1, "Available"),
                ("Vardhman Fibers", "Polyester", 130, 4.7, 3, 4.8, "Available"),
                ("Nandi Dye Chem", "Dye", 320, 4.3, 4, 4.4, "Available"),
                ("SriKrishna Traders", "Chemical", 180, 3.9, 7, 3.8, "Limited"),
            ]
            cur.executemany(
                """INSERT INTO suppliers (name, material_supplied, price_per_unit, quality_rating,
                   avg_delivery_days, rating, availability) VALUES (?,?,?,?,?,?,?)""",
                suppliers
            )
        conn.commit()
        logger.info("Seed data ensured.")


def fetch_all(query, params=()):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


def fetch_one(query, params=()):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None


def execute(query, params=()):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.lastrowid
