import unittest
from unittest.mock import patch, MagicMock
from task_manager import TaskManager

# Constants to avoid hardcoding
TASK_ID = 1
TASK_NAME = "Test"
TASK_PRIORITY = "High"
TASK_DUE_DATE = "2025-12-31"
TASK_COMPLETED = 0

class TestTaskManagerWithMock(unittest.TestCase):
    @patch("task_manager.sqlite3.connect")
    def test_add_task_success(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        tm = TaskManager()
        tm.db_name = "mock.db"
        tm.add_task(TASK_NAME, TASK_PRIORITY, TASK_DUE_DATE)

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("task_manager.sqlite3.connect")
    def test_view_tasks(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (TASK_ID, TASK_NAME, TASK_PRIORITY, TASK_DUE_DATE, TASK_COMPLETED)
        ]

        tm = TaskManager()
        tm.db_name = "mock.db"
        tasks = tm.get_all_tasks(show_completed=False)

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0][1], TASK_NAME)

    @patch("task_manager.sqlite3.connect")
    def test_update_task(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        tm = TaskManager()
        tm.db_name = "mock.db"
        tm.update_task(TASK_ID, True)

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("task_manager.sqlite3.connect")
    def test_delete_task(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        tm = TaskManager()
        tm.db_name = "mock.db"
        tm.delete_task(TASK_ID)

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_add_task_invalid_inputs(self):
        tm = TaskManager()
        tm.db_name = "mock.db"

        with self.assertRaises(ValueError):
            tm.add_task("", TASK_PRIORITY, TASK_DUE_DATE)

        with self.assertRaises(ValueError):
            tm.add_task(TASK_NAME, "Invalid", TASK_DUE_DATE)

        with self.assertRaises(ValueError):
            tm.add_task(TASK_NAME, TASK_PRIORITY, "2025/12/31")

    def test_update_delete_invalid_id(self):
        tm = TaskManager()
        tm.db_name = "mock.db"

        with self.assertRaises(ValueError):
            tm.update_task("abc", True)

        with self.assertRaises(ValueError):
            tm.delete_task(-10)


if __name__ == "__main__":
    unittest.main()
