import sqlite3

def init_db():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    # Create tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            due_date TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")