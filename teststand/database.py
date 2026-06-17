import sqlite3
from contextlib import contextmanager
from pathlib import Path

from werkzeug.security import generate_password_hash

from config import DATABASE_PATH, MIN_PASSWORD_LENGTH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    UNIQUE(user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    order_number TEXT NOT NULL UNIQUE,
    total REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS api_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'general',
    owner_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
"""

TEST_USERS = [
    {"email": "alice@example.com", "password": "password123", "name": "Alice Tester"},
    {"email": "bob@example.com", "password": "password123", "name": "Bob Tester"},
]

PRODUCTS = [
    {"name": "Python Handbook", "description": "A concise guide to Python programming.", "price": 29.99},
    {"name": "Playwright in Action", "description": "End-to-end testing with Playwright.", "price": 39.99},
    {"name": "API Testing Cookbook", "description": "Recipes for REST API test automation.", "price": 24.99},
    {"name": "Test Data Builder", "description": "Patterns for predictable test fixtures.", "price": 19.99},
    {"name": "Locators Guide", "description": "Stable selectors for UI automation.", "price": 14.99},
]

API_ITEMS = [
    {"title": "Write login tests", "description": "Cover happy path and invalid credentials.", "category": "testing"},
    {"title": "Practice pagination", "description": "Assert page boundaries and filters.", "category": "api"},
    {"title": "Handle 401 responses", "description": "Verify unauthorized access is blocked.", "category": "api"},
]


def ensure_data_dir() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    ensure_data_dir()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def seed_data() -> None:
    with get_connection() as conn:
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count == 0:
            for user in TEST_USERS:
                conn.execute(
                    "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
                    (user["email"], generate_password_hash(user["password"]), user["name"]),
                )

        product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if product_count == 0:
            for product in PRODUCTS:
                conn.execute(
                    "INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                    (product["name"], product["description"], product["price"]),
                )

        api_item_count = conn.execute("SELECT COUNT(*) FROM api_items").fetchone()[0]
        if api_item_count == 0:
            alice = conn.execute(
                "SELECT id FROM users WHERE email = ?", ("alice@example.com",)
            ).fetchone()
            if alice:
                for item in API_ITEMS:
                    conn.execute(
                        "INSERT INTO api_items (title, description, category, owner_id) VALUES (?, ?, ?, ?)",
                        (item["title"], item["description"], item["category"], alice["id"]),
                    )


def reset_db() -> None:
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
    init_db()
    seed_data()


def get_user_by_email(email: str):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()


def get_user_by_id(user_id: int):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_user(email: str, password: str, name: str):
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError("password_too_short")
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email.lower(),)).fetchone()
        if existing:
            raise ValueError("email_taken")
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            (email.lower(), generate_password_hash(password), name),
        )
        return cursor.lastrowid
