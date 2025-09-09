import os
import gzip
import json
import psycopg2
from psycopg2.extras import execute_values

# Load DB connection info from environment variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

BULK_FILE = "bulk_opinions.jsonl.gz"  # Change to your file path

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS
)
cur = conn.cursor()

# Create table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS opinions (
    id TEXT PRIMARY KEY,
    case_name TEXT,
    date_filed DATE,
    court TEXT,
    citation TEXT,
    url TEXT,
    plain_text TEXT
)
""")
conn.commit()

batch = []
batch_size = 500
row_count = 0

with gzip.open(BULK_FILE, 'rt', encoding='utf-8') as f:
    for line in f:
        try:
            item = json.loads(line)
            batch.append((
                item.get("id"),
                item.get("caseName", ""),
                item.get("dateFiled", None),
                item.get("court", ""),
                item.get("citations", [{}])[0].get("cite", "") if item.get("citations") else "",
                "https://www.courtlistener.com" + item.get("absolute_url", ""),
                item.get("plain_text", "")
            ))
            row_count += 1
            if len(batch) >= batch_size:
                execute_values(
                    cur,
                    """
                    INSERT INTO opinions (id, case_name, date_filed, court, citation, url, plain_text)
                    VALUES %s
                    ON CONFLICT (id) DO NOTHING
                    """,
                    batch
                )
                conn.commit()
                batch = []
                if row_count % 10000 == 0:
                    print(f"Inserted {row_count} rows...")
        except Exception as e:
            print(f"Error parsing line: {e}")

# Insert any remaining rows
if batch:
    execute_values(
        cur,
        """
        INSERT INTO opinions (id, case_name, date_filed, court, citation, url, plain_text)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """,
        batch
    )
    conn.commit()

cur.close()
conn.close()
print("✅ Bulk data inserted into Supabase")
