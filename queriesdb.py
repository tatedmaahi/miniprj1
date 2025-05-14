import sqlite3
import json

conn = sqlite3.connect('document_database.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT * FROM documents;")
rows = cursor.fetchall()

for row in rows:
    print(f"ID: {row['id']}")
    print(f"Filename: {row['filename']}")
    print(f"Filetype: {row['filetype']}")
    print(f"Filesize: {row['filesize']} bytes")
    print(f"Upload Date: {row['upload_date']}")
    metadata = json.loads(row['metadata'])
    print(f"Metadata: {metadata}")
    print("-" * 50)

conn.close()
