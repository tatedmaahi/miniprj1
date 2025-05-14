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
            if not text or not text.strip():
                logger.warning("Text is empty or contains only whitespace")
                return []
            
            # Simple text preprocessing: lowercase, remove punctuation, split into words
            words = re.findall(r'\b\w+\b', text.lower())
            if not words:
                logger.warning("No valid words found after preprocessing")
                return []
            
            # Create a vocabulary of the top 100 most frequent words
            word_counts = Counter(words)
            top_words = [word for word, _ in word_counts.most_common(100)]
            if not top_words:
                logger.warning("No top words identified after counting")
                return []
            
            # Create a vector: frequency of each top word in the text
            vector = [word_counts[word] for word in top_words]
            logger.debug(f"Generated vector with length {len(vector)}")
            return vector
        
        except Exception as e:
            logger.error(f"Failed to convert text to vector: {str(e)}")
            return []

    def cosine_similarity(self, vec1, vec2):
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def search_documents(self):
        logger.debug("Received search request")
        
        # Get query parameters
        query = request.args.get('query', '').strip()
        search_type = request.args.get('type', 'metadata')  # Default to metadata search
        
        if not query:
            logger.warning("No query provided")
            return jsonify({'error': 'Query parameter is required'}), 400
        
        conn = self.get_db()
        cursor = conn.cursor()
        
        results = []
        
        if search_type == 'metadata':
            # Search by filename or category using LIKE
            logger.debug(f"Performing metadata search for query: {query}")
            query_pattern = f'%{query}%'
            cursor.execute(
                'SELECT id, filename, category, upload_date, file_path, content_vector '
                'FROM documents WHERE filename LIKE ? OR category LIKE ?',
                (query_pattern, query_pattern)
            )
            rows = cursor.fetchall()
            for row in rows:
                results.append({
                    'id': row['id'],
                    'filename': row['filename'],
                    'category': row['category'],
                    'upload_date': row['upload_date'],
                    'file_path': row['file_path']
                })
        
        elif search_type == 'vector':
            # Search by content vector using cosine similarity
            logger.debug(f"Performing vector search for query: {query}")
            query_vector = self.text_to_vector(query)
            if not query_vector:
                logger.warning("Query vector is empty")
                conn.close()
                return jsonify({'error': 'Could not process query for vector search'}), 400
            
            cursor.execute('SELECT id, filename, category, upload_date, file_path, content_vector FROM documents')
            rows = cursor.fetchall()
            
            for row in rows:
                stored_vector = json.loads(row['content_vector'])
                similarity = self.cosine_similarity(query_vector, stored_vector)
                if similarity > 0.1:  # Threshold for relevance
                    results.append({
                        'id': row['id'],
                        'filename': row['filename'],
                        'category': row['category'],
                        'upload_date': row['upload_date'],
                        'file_path': row['file_path'],
                        'similarity': similarity
                    })
            
            # Sort results by similarity (highest to lowest)
            results.sort(key=lambda x: x['similarity'], reverse=True)
        
        else:
            logger.warning(f"Invalid search type: {search_type}")
            conn.close()
            return jsonify({'error': 'Invalid search type. Use "metadata" or "vector"'}), 400
        
        conn.close()
        logger.debug(f"Found {len(results)} matching documents")
        return jsonify({'results': results}), 200

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
            # Check file size (limit to 10 MB)
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)  # Reset file pointer to the beginning
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"File too large: {file_size} bytes (max {MAX_FILE_SIZE} bytes)")
                return jsonify({'error': f'File too large. Maximum allowed size is {MAX_FILE_SIZE // (1024 * 1024)} MB'}), 400
            
            filename = file.filename
            file_path = os.path.join(self.upload_folder, filename)
            logger.debug(f"Saving file to {file_path}")
            file.save(file_path)
            
            try:
                # Extract text and convert to vector
                file_extension = os.path.splitext(filename)[1].lower()
                text = self.extract_text(file_path, file_extension)
                content_vector = self.text_to_vector(text)
                
                if not content_vector:  # Check if vector is empty
                    logger.warning("Content vector is empty, cannot proceed with upload")
                    raise Exception("Failed to generate content vector for the document")
                
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
            
            except Exception as e:
                # Cleanup: Remove the file if any step fails after saving
                logger.error(f"Upload failed, cleaning up: {e}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Removed file: {file_path}")
                return jsonify({'error': f'Upload failed: {str(e)}'}), 500
        
        logger.warning("Invalid file type")
        return jsonify({'error': 'Only PDF and .md files allowed'}), 400

    def setup_routes(self):
        @self.app.route('/upload', methods=['POST'])
        def upload():
            return self.handle_upload()

        @self.app.route('/search', methods=['GET'])
        def search():
            return self.search_documents()

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