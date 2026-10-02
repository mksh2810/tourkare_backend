import sqlite3
from pathlib import Path

# Always store the database inside the backend directory,
# regardless of where the server is started from.
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "tourkare.db"


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)

    # Allows us to access columns by their names.
    conn.row_factory = sqlite3.Row

    # Enable foreign key constraints.
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def init_db():
    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                destination TEXT NOT NULL,
                days INTEGER NOT NULL,
                budget REAL NOT NULL,
                interests TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS itinerary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (trip_id)
                    REFERENCES trips(id)
                    ON DELETE CASCADE
            )
        """)

        conn.commit()

    finally:
        conn.close()