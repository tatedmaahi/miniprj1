import sqlite3
import json
conn = sqlite3.connect('documents.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT * FROM documents;")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row['id']}")
    print(f"Filename: {row['filename']}")
    print(f"Category: {row['category']}")
    print(f"Upload Date: {row['upload_date']}")
    print(f"File Path: {row['file_path']}")
    vector = json.loads(row['content_vector'])
    print(f"Content Vector: {vector[:5]}... (first 5 elements, total length: {len(vector)})")
    print("-" * 50)
conn.close()