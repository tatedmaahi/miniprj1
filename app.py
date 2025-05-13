from flask import Flask, request, jsonify
import os
import sqlite3
import logging
import json
from PyPDF2 import PdfReader
from collections import Counter
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DocumentManager:
    def __init__(self):
        self.app = Flask(__name__)
        self.upload_folder = 'uploads'
        self.db_path = 'documents.db'
        
        logger.debug("Initializing DocumentManager")
        
        # Create uploads directory
        os.makedirs(self.upload_folder, exist_ok=True)
        logger.debug(f"Created uploads directory: {self.upload_folder}")
        
        # Initialize database
        self.init_db()
        
        # Set up routes
        self.setup_routes()

    def init_db(self):
        # Define the schema with content_vector column
        schema = '''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            category TEXT NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT NOT NULL,
            content_vector TEXT NOT NULL
        );
        '''
        
        # Check if database is valid by trying to query the documents table
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents';")
            result = cursor.fetchone()
            if not result:
                logger.debug("Documents table does not exist. Creating it.")
                conn.executescript(schema)
                conn.commit()
            else:
                # Check if content_vector column exists, add it if not
                cursor.execute("PRAGMA table_info(documents);")
                columns = [col[1] for col in cursor.fetchall()]
                if 'content_vector' not in columns:
                    logger.debug("Adding content_vector column to documents table")
                    cursor.execute("ALTER TABLE documents ADD COLUMN content_vector TEXT NOT NULL DEFAULT '[]';")
                    conn.commit()
            conn.close()
            logger.debug(f"Database is valid at {self.db_path}")
        except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
            logger.warning(f"Invalid database: {e}. Recreating database.")
            # Delete the invalid database file
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            # Create a new database
            conn = sqlite3.connect(self.db_path)
            conn.executescript(schema)
            conn.commit()
            conn.close()
            logger.debug("Database initialized")

    def get_db(self):
        logger.debug("Connecting to database")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def extract_text(self, file_path, file_extension):
        logger.debug(f"Extracting text from {file_path}")
        try:
            if file_extension == '.pdf':
                reader = PdfReader(file_path)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() or ''
                return text
            elif file_extension == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ''
        return ''

    def text_to_vector(self, text):
        logger.debug("Converting text to Bag-of-Words vector")
        try:
            if not text.strip():
                return []
            # Simple text preprocessing: lowercase, remove punctuation, split into words
            words = re.findall(r'\b\w+\b', text.lower())
            if not words:
                return []
            # Create a vocabulary of the top 100 most frequent words
            word_counts = Counter(words)
            top_words = [word for word, _ in word_counts.most_common(100)]
            if not top_words:
                return []
            # Create a vector: frequency of each top word in the text
            vector = [word_counts[word] for word in top_words]
            return vector
        except Exception as e:
            logger.error(f"Error converting text to vector: {e}")
            return []

    def handle_upload(self):
        logger.debug("Received upload request")
        
        if 'file' not in request.files:
            logger.warning("No file in request")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        category = request.form.get('category', 'Uncategorized')
        logger.debug(f"File: {file.filename}, Category: {category}")
        
        if file.filename == '':
            logger.warning("No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        if file and (file.filename.endswith('.pdf') or file.filename.endswith('.md')):
            filename = file.filename
            file_path = os.path.join(self.upload_folder, filename)
            logger.debug(f"Saving file to {file_path}")
            file.save(file_path)
            
            # Extract text and convert to vector
            file_extension = os.path.splitext(filename)[1].lower()
            text = self.extract_text(file_path, file_extension)
            content_vector = self.text_to_vector(text)
            vector_json = json.dumps(content_vector)  # Serialize vector as JSON string
            
            # Save metadata and vector
            logger.debug("Saving metadata and vector to database")
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO documents (filename, category, file_path, content_vector) VALUES (?, ?, ?, ?)',
                (filename, category, file_path, vector_json)
            )
            conn.commit()
            conn.close()
            logger.debug("Metadata and vector saved")
            
            logger.info("File uploaded successfully")
            return jsonify({'message': 'File uploaded successfully'}), 200
        
        logger.warning("Invalid file type")
        return jsonify({'error': 'Only PDF and .md files allowed'}), 400

    def setup_routes(self):
        @self.app.route('/upload', methods=['POST'])
        def upload():
            return self.handle_upload()

    def run(self):
        logger.debug("Starting Flask server")
        self.app.run(debug=True)

if __name__ == '__main__':
    # Delete existing database to start fresh
    if os.path.exists('documents.db'):
        os.remove('documents.db')
        logger.info("Deleted existing documents.db to start fresh")
    
    manager = DocumentManager()
    manager.run()