import sqlite3
import os
import platform
import logging  # Added for debugging
from dotenv import load_dotenv  # Added to load .env file
from queries import (  # Import SQL queries
    SELECT_ALL_TASKS,
    SELECT_PENDING_TASKS,
    INSERT_TASK,
    UPDATE_TASK_COMPLETED,
    DELETE_TASK,
    COUNT_PENDING_TASKS,
    COUNT_COMPLETED_TASKS,
)

# Set up logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()
DB_NAME = os.getenv("DB_NAME")

class TaskManager:
    def __init__(self):
        self.db_name = DB_NAME
        # Ensure the database exists
        if not os.path.exists(self.db_name):
            from database import init_db
            init_db()

    def add_task(self, description, priority, due_date):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(INSERT_TASK, (description, priority, due_date))
        conn.commit()
        conn.close()
        logging.info(f"Task added: {description}")
        print("Task added!")

    def get_all_tasks(self, show_completed):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if show_completed:
            cursor.execute(SELECT_ALL_TASKS)
        else:
            cursor.execute(SELECT_PENDING_TASKS)
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def view_tasks(self, show_completed):
        tasks = self.get_all_tasks(show_completed)
        if not tasks:
            print("No tasks found.")
        else:
            for task in tasks:
                status = "Completed" if task[4] else "Pending"
                print(f"ID: {task[0]} | {task[1]} | {task[2]} | Due: {task[3]} | {status}")

    def update_task(self, task_id, completed):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(UPDATE_TASK_COMPLETED, (1 if completed else 0, task_id))
        conn.commit()
        conn.close()
        logging.info(f"Task {task_id} updated: completed={completed}")
        print("Task updated!")

    def delete_task(self, task_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(DELETE_TASK, (task_id,))
        conn.commit()
        conn.close()
        logging.info(f"Task {task_id} deleted")
        print("Task deleted!")

    def get_statistics(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(COUNT_PENDING_TASKS)
        pending = cursor.fetchone()[0]
        cursor.execute(COUNT_COMPLETED_TASKS)
        completed = cursor.fetchone()[0]
        conn.close()

        total = pending + completed
        print(f"Total Tasks: {total}")
        print(f"Pending: {pending}")
        print(f"Completed: {completed}")
        if total > 0:
            print(f"Completion Rate: {(completed / total) * 100}%")

def main():
    tm = TaskManager()
    
    while True:
        
        print("\nTask Manager")
        print("1. Add Task")
        print("2. View Tasks")
        print("3. Mark Task as Completed")
        print("4. Delete Task")
        print("5. View Stats")
        print("6. Exit")
        choice = input("Choose (1-6): ")

        if choice == "1":
            description = input("Task description: ")
            priority = input("Priority (Low/Medium/High): ")
            due_date = input("Due date (YYYY-MM-DD): ")
            tm.add_task(description, priority, due_date)

        elif choice == "2":
            show_completed = input("Show completed tasks? (y/n): ").lower() == "y"
            tm.view_tasks(show_completed)

        elif choice == "3":
            task_id = input("Task ID to mark as completed: ")
            tm.update_task(int(task_id), True)

        elif choice == "4":
            task_id = input("Task ID to delete: ")
            tm.delete_task(int(task_id))

        elif choice == "5":
            tm.get_statistics()

        elif choice == "6":
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()