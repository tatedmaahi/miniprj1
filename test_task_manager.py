import unittest
from unittest.mock import patch, Mock
import sqlite3
import os
from task_manager import TaskManager, main
from queries import (
    SELECT_ALL_TASKS,
    SELECT_PENDING_TASKS,
    INSERT_TASK,
    UPDATE_TASK_COMPLETED,
    DELETE_TASK,
    COUNT_PENDING_TASKS,
    COUNT_COMPLETED_TASKS,
)

# Mock task data for testing
MOCK_TASKS = [
    (1, "Task 1", "Low", "2025-12-31", 0),
    (2, "Task 2", "High", "2025-12-30", 1),
]

class TestTaskManager(unittest.TestCase):
    def setUp(self):
        # Mock environment variable for DB_NAME
        self.patcher = patch('task_manager.os.getenv', return_value=":memory:")
        self.patcher.start()
        self.tm = TaskManager()

    def tearDown(self):
        self.patcher.stop()

    @patch('task_manager.sqlite3.connect')
    def test_init_db(self, mock_connect):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = None
        mock_conn.commit.return_value = None
        mock_conn.close.return_value = None

        self.tm.init_db()
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('task_manager.sqlite3.connect')
    def test_add_task_success(self, mock_connect):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = None
        mock_conn.commit.return_value = None
        mock_conn.close.return_value = None

        self.tm.add_task("Test task", "Medium", "2025-12-31")
        mock_cursor.execute.assert_called_once_with(INSERT_TASK, ("Test task", "Medium", "2025-12-31"))
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_add_task_invalid_description(self):
        with self.assertRaises(ValueError) as context:
            self.tm.add_task("", "Medium", "2025-12-31")
        self.assertEqual(str(context.exception), "Task description cannot be empty")

    def test_add_task_invalid_priority(self):
        with self.assertRaises(ValueError) as context:
            self.tm.add_task("Test task", "Invalid", "2025-12-31")
        self.assertEqual(str(context.exception), "Priority must be Low, Medium, or High")

    def test_add_task_invalid_due_date(self):
        with self.assertRaises(ValueError) as context:
            self.tm.add_task("Test task", "Medium", "2025-13-31")
        self.assertEqual(str(context.exception), "Due date must be in YYYY-MM-DD format")

    @patch('task_manager.sqlite3.connect')
    def test_get_all_tasks(self, mock_connect):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = MOCK_TASKS
        mock_conn.close.return_value = None

        # Test with show_completed=True
        mock_cursor.execute.return_value = None
        result = self.tm.get_all_tasks(show_completed=True)
        mock_cursor.execute.assert_called_once_with(SELECT_ALL_TASKS)
        self.assertEqual(result, MOCK_TASKS)

        # Test with show_completed=False
        mock_cursor.execute.reset_mock()
        result = self.tm.get_all_tasks(show_completed=False)
        mock_cursor.execute.assert_called_once_with(SELECT_PENDING_TASKS)
        self.assertEqual(result, MOCK_TASKS)

    @patch('task_manager.sqlite3.connect')
    def test_update_task_success(self, mock_connect):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = None
        mock_conn.commit.return_value = None
        mock_conn.close.return_value = None

        self.tm.update_task(1, True)
        mock_cursor.execute.assert_called_once_with(UPDATE_TASK_COMPLETED, (1, 1))
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_update_task_invalid_id(self):
        with self.assertRaises(ValueError) as context:
            self.tm.update_task("invalid", True)
        self.assertEqual(str(context.exception), "Task ID must be a positive integer")

    @patch('task_manager.sqlite3.connect')
    def test_delete_task_success(self, mock_connect):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = None
        mock_conn.commit.return_value = None
        mock_conn.close.return_value = None

        self.tm.delete_task(1)
        mock_cursor.execute.assert_called_once_with(DELETE_TASK, (1,))
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('task_manager.sqlite3.connect')
    def test_get_statistics(self, mock_connect):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [(1,), (1,)]  # Mock pending and completed counts
        mock_conn.close.return_value = None

        with patch('builtins.print') as mocked_print:
            self.tm.get_statistics()
            mock_cursor.execute.assert_any_call(COUNT_PENDING_TASKS)
            mock_cursor.execute.assert_any_call(COUNT_COMPLETED_TASKS)
            mocked_print.assert_any_call("Total Tasks: 2")
            mocked_print.assert_any_call("Pending: 1")
            mocked_print.assert_any_call("Completed: 1")
            mocked_print.assert_any_call("Completion Rate: 50.0%")

    @patch('task_manager.TaskManager')
    @patch('builtins.input', side_effect=['1', 'Test task', 'Medium', '2025-12-31', '6'])
    @patch('builtins.print')
    def test_main_add_task_flow(self, mock_print, mock_input, mock_task_manager):
        mock_instance = Mock()
        mock_task_manager.return_value = mock_instance
        main()
        mock_instance.add_task.assert_called_once_with("Test task", "Medium", "2025-12-31")
        mock_print.assert_any_call("Goodbye!")

if __name__ == "__main__":
    unittest.main()