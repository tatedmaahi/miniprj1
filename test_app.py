import unittest
from app import DocumentManager
import sqlite3
import os
import json
from flask import json as flask_json
from flask.testing import FlaskClient

class TestDocumentManager(unittest.TestCase):
    def setUp(self):
        self.manager = DocumentManager()
        self.manager.db_path = 'test_documents.db'
        self.manager.upload_folder = 'test_uploads'
        os.makedirs(self.manager.upload_folder, exist_ok=True)
        self.manager.init_db()

    def tearDown(self):
        os.remove(self.manager.db_path)
        import shutil
        shutil.rmtree(self.manager.upload_folder)

    def test_init_db(self):
        conn = sqlite3.connect(self.manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents';")
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        conn.close()

    def test_get_db(self):
        conn = self.manager.get_db()
        self.assertIsInstance(conn, sqlite3.Connection)
        conn.close()

    def test_extract_text_pdf(self):
        file_path = os.path.join('uploads', 'LOG SHEET.pdf')
        text = self.manager.extract_text(file_path, '.pdf')
        self.assertIsInstance(text, str)

    def test_text_to_vector(self):
        text = 'This is a test sentence.'
        vector = self.manager.text_to_vector(text)
        self.assertIsInstance(vector, list)

    def test_cosine_similarity(self):
        vec1 = [1, 2, 3]
        vec2 = [4, 5, 6]
        similarity = self.manager.cosine_similarity(vec1, vec2)
        self.assertGreaterEqual(similarity, 0)
        self.assertLessEqual(similarity, 1)

class TestDocumentManagerIntegration(unittest.TestCase):

    def setUp(self):
        self.manager = DocumentManager()
        self.manager.db_path = 'test_documents.db'
        self.manager.upload_folder = 'test_uploads'
        os.makedirs(self.manager.upload_folder, exist_ok=True)
        self.manager.init_db()
        self.app = self.manager.app.test_client()

    def tearDown(self):
        os.remove(self.manager.db_path)
        import shutil
        shutil.rmtree(self.manager.upload_folder)

    def test_upload_file(self):
        file_path = os.path.join('uploads', 'LOG SHEET.pdf')
        with open(file_path, 'rb') as f:
            response = self.app.post('/upload', data={'file': (f, 'LOG SHEET.pdf'), 'category': 'personal'}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)

    def test_search_documents(self):
        # Upload the file
        file_path = os.path.join('uploads', 'LOG SHEET.pdf')
        with open(file_path, 'rb') as f:
            self.app.post('/upload', data={'file': (f, 'LOG SHEET.pdf'), 'category': 'personal'}, content_type='multipart/form-data')

        # Search for the file
        response = self.app.get('/search', query_string={'query': 'LOG SHEET', 'type': 'metadata'})
        self.assertEqual(response.status_code, 200)
        data = flask_json.loads(response.data)
        self.assertGreater(len(data['results']), 0)

if __name__ == '__main__':
    unittest.main()

