import sqlite3
import os

DB_PATH = "data/Lee.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print("DB not found at", DB_PATH)
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("ALTER TABLE expenses ADD COLUMN type TEXT DEFAULT 'expense'")
    except sqlite3.OperationalError:
        pass # Already exists

    try:
        conn.execute("ALTER TABLE expenses ADD COLUMN sub_category TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE expenses ADD COLUMN status TEXT DEFAULT 'confirmed'")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("Migration successful")

if __name__ == "__main__":
    migrate()
