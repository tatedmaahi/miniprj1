import sqlite3
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

conn = sqlite3.connect('document_database.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT * FROM documents;")
rows = cursor.fetchall()

for row in rows:
    logger.info(f"ID: {row['id']}")
    logger.info(f"Filename: {row['filename']}")
    logger.info(f"Filetype: {row['filetype']}")
    logger.info(f"Filesize: {row['filesize']} bytes")
    logger.info(f"Upload Date: {row['upload_date']}")
    metadata = json.loads(row['metadata'])
    logger.info(f"Metadata: {metadata}")
    logger.info("-" * 50)

conn.close()