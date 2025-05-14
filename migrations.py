import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
from queries import SELECT_ALL_TASKS  # Import the required query

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
OLD_DB_NAME = os.getenv("DB_NAME")
NEW_DB_NAME = os.getenv("NEW_DB_NAME", "tasks_new.db")

# Define the INSERT query for the new schema (override the one from queries.py)
INSERT_TASK = """
    INSERT INTO tasks (id, description, priority, due_date, completed, created_at, updated_at, completed_at, deleted_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

def create_new_schema(new_db):
    """Create the new database schema with additional fields."""
    conn = sqlite3.connect(new_db)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            due_date TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            completed_at TEXT,
            deleted_at TEXT
        );
    """)
    conn.commit()
    conn.close()
    logging.info("New database schema created successfully")

def migrate_data(old_db, new_db):
    """Migrate data from old database to new database."""
    old_conn = sqlite3.connect(old_db)
    new_conn = sqlite3.connect(new_db)
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()

    # Fetch all tasks from old database using the query from queries.py
    old_cursor.execute(SELECT_ALL_TASKS)
    tasks = old_cursor.fetchall()

    # Get current timestamp
    current_time = datetime.now().isoformat()

    # Insert tasks into new database
    for task in tasks:
        task_id, description, priority, due_date, completed = task
        completed_at = current_time if completed else None
        new_cursor.execute(INSERT_TASK,
                          (task_id, description, priority, due_date, completed, current_time, current_time, completed_at, None))

    new_conn.commit()
    old_conn.close()
    new_conn.close()
    logging.info(f"Migrated {len(tasks)} tasks to new database")

def main():
    if not OLD_DB_NAME:
        raise ValueError("OLD_DB_NAME environment variable not set")
    if not os.path.exists(OLD_DB_NAME):
        raise FileNotFoundError(f"Old database {OLD_DB_NAME} does not exist")

    # Create new database
    create_new_schema(NEW_DB_NAME)

    # Migrate data
    migrate_data(OLD_DB_NAME, NEW_DB_NAME)

    print(f"Migration completed. New database created at {NEW_DB_NAME}")

if __name__ == "__main__":
    main()