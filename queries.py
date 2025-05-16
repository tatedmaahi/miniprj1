SELECT_ALL_TASKS = "SELECT * FROM tasks"
SELECT_PENDING_TASKS = "SELECT * FROM tasks WHERE completed = 0"
INSERT_TASK = "INSERT INTO tasks (description, priority, due_date) VALUES (?, ?, ?)"
UPDATE_TASK_COMPLETED = "UPDATE tasks SET completed = ? WHERE id = ?"
DELETE_TASK = "DELETE FROM tasks WHERE id = ?"
COUNT_PENDING_TASKS = "SELECT COUNT(*) FROM tasks WHERE completed = 0"
COUNT_COMPLETED_TASKS = "SELECT COUNT(*) FROM tasks WHERE completed = 1"

