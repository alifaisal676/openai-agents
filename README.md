# CourtListener Bulk Data Loader for Supabase

This script loads bulk CourtListener opinions data from a `.jsonl.gz` file into a Supabase Postgres database.

## Requirements
- Python 3.8+
- `psycopg2-binary` package (`pip install psycopg2-binary`)
- A bulk data file from CourtListener (e.g., `bulk_opinions.jsonl.gz`)
- Supabase/Postgres database credentials

## Setup
1. **Set environment variables** for your database connection:
   - `DB_HOST` (database host)
   - `DB_PORT` (database port, default: 5432)
   - `DB_NAME` (database name)
   - `DB_USER` (database user)
   - `DB_PASS` (database password)

2. **Place your bulk data file** (e.g., `bulk_opinions.jsonl.gz`) in the project directory.
   - You can download bulk data from [CourtListener Bulk Data](https://www.courtlistener.com/api/bulk-data/).

3. **Install dependencies:**
   ```sh
   pip install psycopg2-binary
   ```

## Usage
Run the loader script:
```sh
python bulk_to_supabase.py
```

- The script will stream the bulk data file line by line and insert records into the `opinions` table in your Supabase/Postgres database.
- Progress is printed every 10,000 rows.
- At the end, you'll see: `✅ Bulk data inserted into Supabase`

## Table Schema
The script will create the following table if it does not exist:

| Column      | Type | Description                |
|-------------|------|----------------------------|
| id          | text | Opinion ID (primary key)   |
| case_name   | text | Case name                  |
| date_filed  | date | Date filed                 |
| court       | text | Court name                 |
| citation    | text | First citation (if any)    |
| url         | text | Full opinion URL           |
| plain_text  | text | Full opinion text          |

## Notes
- The script uses batch inserts for performance and skips duplicates.
- You can change the bulk data file path in the script if needed.
- For large datasets, the script is memory-efficient and robust.

---
For questions or improvements, open an issue or pull request.
