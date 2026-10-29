import sqlite3
import os
import contextlib
from flask import has_app_context, current_app

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "finance.db")

def get_db_path():
    if has_app_context() and current_app and current_app.config.get("DATABASE_PATH"):
        return current_app.config["DATABASE_PATH"]
    
    # Check if running in Vercel or read-only serverless environment
    if os.environ.get("VERCEL"):
        tmp_db = "/tmp/finance.db"
        if not os.path.exists(tmp_db) and os.path.exists(DEFAULT_DB_PATH):
            import shutil
            try:
                shutil.copy2(DEFAULT_DB_PATH, tmp_db)
            except Exception:
                pass
        return tmp_db

    return os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection(db_path=None):
    if db_path is None:
        db_path = get_db_path()
    
    # Ensure directory exists if path contains directories
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        pass
    return conn

@contextlib.contextmanager
def get_db(db_path=None):
    conn = get_db_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db(db_path=None):
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT,
            currency TEXT DEFAULT 'USD',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Accounts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            type TEXT NOT NULL, -- checking, savings, credit_card, investment, cash
            balance REAL NOT NULL DEFAULT 0.0,
            initial_balance REAL NOT NULL DEFAULT 0.0,
            currency TEXT DEFAULT 'USD',
            account_number TEXT,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 3. Categories table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            type TEXT NOT NULL, -- income, expense
            color TEXT DEFAULT '#3B82F6',
            icon TEXT DEFAULT 'tag',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 4. Transactions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
            to_account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            type TEXT NOT NULL, -- income, expense, transfer
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            notes TEXT,
            tags TEXT,
            is_cleared INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 5. Budgets table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            amount_limit REAL NOT NULL,
            period TEXT DEFAULT 'monthly',
            month TEXT, -- YYYY-MM
            alert_threshold REAL DEFAULT 0.8,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, category_id, month)
        );
        """)

        # 6. Savings Goals table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL NOT NULL DEFAULT 0.0,
            target_date TEXT,
            color TEXT DEFAULT '#10B981',
            notes TEXT,
            is_completed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 7. Goal Contributions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS goal_contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL REFERENCES savings_goals(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Seed standard categories if none exist
        cursor.execute("SELECT COUNT(*) as cnt FROM categories WHERE user_id IS NULL;")
        row = cursor.fetchone()
        if row and row["cnt"] == 0:
            default_categories = [
                # Income
                ("Pocket Money / Parents Allowance", "income", "#10B981", "cash"),
                ("Freelance & Part-time Tutoring", "income", "#059669", "briefcase"),
                ("College Stipend & Awards", "income", "#34D399", "award"),
                ("Cash Gift / Festival", "income", "#6EE7B7", "gift"),
                # Expense
                ("College Canteen & Mess", "expense", "#F59E0B", "coffee"),
                ("Snacks, Swiggy & Zomato", "expense", "#F97316", "shopping-cart"),
                ("Books, Xerox & Stationery", "expense", "#6366F1", "book"),
                ("Hostel / PG Room Rent", "expense", "#EF4444", "home"),
                ("Metro, Bus & Bike Petrol", "expense", "#3B82F6", "truck"),
                ("Mobile Recharge & Internet", "expense", "#0EA5E9", "zap"),
                ("Movies & Hangouts with Friends", "expense", "#EC4899", "film"),
                ("College Fest & Lab Materials", "expense", "#8B5CF6", "tag"),
                ("Miscellaneous", "expense", "#6B7280", "archive"),
            ]
            cursor.executemany(
                "INSERT INTO categories (name, type, color, icon, user_id) VALUES (?, ?, ?, ?, NULL);",
                default_categories
            )
