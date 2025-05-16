from flask import Flask, request, jsonify
import os
import sqlite3
import logging
import json
from datetime import datetime
from file_handlers import Loader  # Import the new Loader class

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DocumentManager:
    def __init__(self):
        self.app = Flask(__name__)
        self.upload_folder = 'Uploads'
        self.db_path = 'document_database.db'
        self.loader = Loader()  # Initialize the Loader class
        
        logger.debug("Initializing DocumentManager")
        
        # Create uploads directory
        os.makedirs(self.upload_folder, exist_ok=True)
        logger.debug(f"Created uploads directory: {self.upload_folder}")
        
        # Initialize database
        self.init_db()
        
        # Set up routes
        self.setup_routes()

    def init_db(self):
        schema = '''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filetype TEXT NOT NULL,
            filesize INTEGER NOT NULL,
            upload_date TEXT NOT NULL,
            metadata TEXT NOT NULL,
            content_vector TEXT NOT NULL DEFAULT '[]'
        );
        '''
        
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
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
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
                doc = fitz.open(file_path)
                text = ''
                for page in doc:
                    text += page.get_text() or ''
                doc.close()
                return text
            elif file_extension == '.docx':
                return docx2txt.process(file_path)
            # Images and SVGs typically don't have extractable text for vectorization
            return ''
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ''

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

    def handle_upload(self):
        logger.debug("Received upload request")
        
        logger.debug(f"Request files: {request.files}")
        logger.debug(f"Request form: {request.form}")
        
        if 'file' not in request.files:
            logger.warning("No file in request")
            return jsonify({'error': 'No file uploaded. Please ensure the file is sent with the key "file".'}), 400
        
        file = request.files['file']
        logger.debug(f"File: {file.filename}")
        
        if file.filename == '':
            logger.warning("No file selected")
            return jsonify({'error': 'No file selected. Please choose a file to upload.'}), 400
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension in ('.jpg', '.jpeg', '.png', '.docx', '.pdf', '.svg'):
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"File too large: {file_size} bytes (max {MAX_FILE_SIZE} bytes)")
                return jsonify({'error': f'File too large. Maximum allowed size is {MAX_FILE_SIZE // (1024 * 1024)} MB'}), 400
            
            filename = file.filename
            file_path = os.path.join(self.upload_folder, filename)
            logger.debug(f"Saving file to {file_path}")
            file.save(file_path)
            
            try:
                loaders = {
                    '.jpg': self.loader.load_image,
                    '.jpeg': self.loader.load_image,
                    '.png': self.loader.load_image,
                    '.docx': self.loader.load_docx,
                    '.pdf': self.loader.load_pdf,
                    '.svg': self.loader.load_svg
                }
                
                metadata, content_vector = loaders[file_extension](file_path)
                metadata_json = json.dumps(metadata)
                vector_json = json.dumps(content_vector)
                
                logger.debug("Saving metadata and vector to database")
                conn = self.get_db()
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO documents (filename, filetype, filesize, upload_date, metadata, content_vector) VALUES (?, ?, ?, ?, ?, ?)',
                    (filename, file_extension, file_size, datetime.now().isoformat(), metadata_json, vector_json)
                )
                conn.commit()
                conn.close()
                logger.debug("Metadata and vector saved")
                
                logger.info("File uploaded successfully")
                return jsonify({'message': 'File uploaded successfully', 'metadata': metadata}), 200
            
            except Exception as e:
                logger.error(f"Upload failed, cleaning up: {e}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Removed file: {file_path}")
                return jsonify({'error': f'Upload failed: {str(e)}'}), 500
        
        logger.warning("Invalid file type")
        return jsonify({'error': 'Only JPG, JPEG, PNG, DOCX, PDF, and SVG files allowed'}), 400

    def search_documents(self):
        logger.debug("Received search request")
        
        search_type = request.args.get('type', 'metadata')  # Default to metadata search
        query = request.args.get('query', '').strip()
        query_image = request.files.get('query_image')  # Optional image file for vector search
        
        if search_type == 'metadata' and not query:
            logger.warning("No query provided for metadata search")
            return jsonify({'error': 'Query parameter is required for metadata search'}), 400
        
        if search_type == 'vector' and not query and not query_image:
            logger.warning("No query or query_image provided for vector search")
            return jsonify({'error': 'Either query (text) or query_image (file) is required for vector search'}), 400
        
        conn = self.get_db()
        cursor = conn.cursor()
        
        results = []
        
        if search_type == 'metadata':
            logger.debug(f"Performing metadata search for query: {query}")
            query_pattern = f'%{query}%'
            cursor.execute(
                'SELECT id, filename, filetype, filesize, upload_date, metadata, content_vector '
                'FROM documents WHERE filename LIKE ? OR filetype LIKE ?',
                (query_pattern, query_pattern)
            )
            rows = cursor.fetchall()
            for row in rows:
                results.append({
                    'id': row['id'],
                    'filename': row['filename'],
                    'filetype': row['filetype'],
                    'filesize': row['filesize'],
                    'upload_date': row['upload_date'],
                    'metadata': json.loads(row['metadata'])
                })
        
        elif search_type == 'vector':
            logger.debug("Performing vector search")
            
            # Determine the query vector type: text for DOCX/PDF, image for images
            if query_image:
                # Validate image file
                file_extension = os.path.splitext(query_image.filename)[1].lower()
                if file_extension not in ('.jpg', '.jpeg', '.png'):
                    logger.warning("Invalid query image type")
                    conn.close()
                    return jsonify({'error': 'Query image must be JPG, JPEG, or PNG'}), 400
                
                try:
                    img = Image.open(query_image)
                    query_vector = self.loader.image_to_vector(img)
                    query_vector_type = 'image'  # Length 768
                except Exception as e:
                    logger.error(f"Error processing query image: {e}")
                    conn.close()
                    return jsonify({'error': f'Failed to process query image: {str(e)}'}), 400
            else:
                # Text-based query for DOCX/PDF
                query_vector = self.loader.text_to_vector(query)
                query_vector_type = 'text'  # Length 100
            
            if not query_vector:
                logger.warning("Query vector is empty")
                conn.close()
                return jsonify({'error': 'Could not process query for vector search'}), 400
            
            cursor.execute('SELECT id, filename, filetype, filesize, upload_date, metadata, content_vector FROM documents')
            rows = cursor.fetchall()
            
            for row in rows:
                stored_vector = json.loads(row['content_vector'])
                file_extension = row['filetype'].lower()
                
                # Determine the stored vector type based on file extension
                if file_extension in ('.jpg', '.jpeg', '.png'):
                    stored_vector_type = 'image'  # Length 768
                elif file_extension in ('.docx', '.pdf'):
                    stored_vector_type = 'text'  # Length 100
                else:
                    stored_vector_type = None  # SVG or others with no vector
                
                # Compare only if vector types match
                if stored_vector_type != query_vector_type:
                    continue
                
                if not stored_vector or len(stored_vector) != len(query_vector):
                    continue
                
                similarity = self.cosine_similarity(query_vector, stored_vector)
                if similarity > 0.1:  # Threshold for relevance
                    results.append({
                        'id': row['id'],
                        'filename': row['filename'],
                        'filetype': row['filetype'],
                        'filesize': row['filesize'],
                        'upload_date': row['upload_date'],
                        'metadata': json.loads(row['metadata']),
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

    def setup_routes(self):
        @self.app.route('/upload', methods=['POST'])
        def upload():
            return self.handle_upload()

        @self.app.route('/search', methods=['GET', 'POST'])  # Allow POST for file uploads
        def search():
            return self.search_documents()

    def run(self):
        logger.debug("Starting Flask server")
        self.app.run(debug=True)

if __name__ == '__main__':
    if os.path.exists('document_database.db'):
        os.remove('document_database.db')
        logger.info("Deleted existing document_database.db to start fresh")
    
    manager = DocumentManager()
    manager.run()