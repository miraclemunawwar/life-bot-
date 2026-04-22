import sqlite3
from config import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            subject TEXT,
            deadline TEXT,
            progress INTEGER DEFAULT 0,
            done INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pair TEXT,
            entry REAL,
            exit_price REAL,
            lot_size REAL,
            setup TEXT,
            result TEXT,
            pnl REAL DEFAULT 0,
            notes TEXT,
            date TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS work_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            client TEXT,
            task TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            source TEXT,
            date TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            mood TEXT,
            date TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS shared_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assigned_by INTEGER,
            assigned_to INTEGER,
            title TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS family_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date TEXT,
            reminded INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            category TEXT,
            note TEXT,
            date TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS commitments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            amount REAL,
            due_date TEXT,
            paid INTEGER DEFAULT 0
        );
    """)

    conn.commit()
    conn.close()
    print("Database ready.")
