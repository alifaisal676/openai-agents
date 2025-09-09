import requests
import sqlite3

# -----------------------------
# 1. Your CourtListener API Token
# -----------------------------
API_TOKEN = "2608364830d3d38e6c97934b18197f13070712eb"  # <-- put your token here
HEADERS = {"Authorization": f"Token {API_TOKEN}"}

# -----------------------------
# 2. Connect to SQLite database
# -----------------------------
conn = sqlite3.connect("courtlistener_small.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS opinions (
    id TEXT PRIMARY KEY,
    case_name TEXT,
    date_filed TEXT,
    court TEXT,
    citation TEXT,
    url TEXT,
    plain_text TEXT
)
""")

# -----------------------------
# 3. Fetch data from API (with authentication)
# -----------------------------
url = "https://www.courtlistener.com/api/rest/v3/opinions/?court=scotus&date_filed__gte=2020-01-01&page_size=20"
response = requests.get(url, headers=HEADERS)
try:
    data = response.json()
    print("API response:", data)
except Exception as e:
    print("Error decoding JSON:", e)
    print("Raw response:", response.text)
    data = {}

# -----------------------------
# 4. Insert into SQLite
# -----------------------------
for item in data.get("results", []):
    cursor.execute("""
        INSERT OR IGNORE INTO opinions 
        (id, case_name, date_filed, court, citation, url, plain_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        item.get("id"),
        item.get("case_name", ""),
        item.get("date_filed", ""),
        item.get("court", ""),
        item.get("citations", [{}])[0].get("cite", "") if item.get("citations") else "",
        "https://www.courtlistener.com" + item.get("absolute_url", ""),
        item.get("plain_text", "")
    ))

conn.commit()
conn.close()

print("✅ Data saved successfully in SQLite: courtlistener_small.db")
