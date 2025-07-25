import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
#!/usr/bin/env python3

import sqlite3
import sys
from pathlib import Path

def connect_db(db_path="lab_reports.db"):
    if not Path(db_path).exists():
        logger.error(f"Database file '{db_path}' not found")
        return None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return None

def show_stats(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM patients")
    patient_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM lab_tests")
    test_count = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT test_name) FROM lab_tests")
    unique_tests = c.fetchone()[0]
    db_size = Path("lab_reports.db").stat().st_size / (1024 * 1024)
    logger.info(f"\nDatabase Stats")
    logger.info(f"Patients: {patient_count}")
    logger.info(f"Lab Tests: {test_count}")
    logger.info(f"Unique Test Types: {unique_tests}")
    logger.info(f"DB Size: {db_size:.2f} MB")

def list_patients(conn):
    c = conn.cursor()
    c.execute("""
        SELECT patient_id, patient_name, age, gender, test_date,
               (SELECT COUNT(*) FROM lab_tests WHERE patient_id = patients.patient_id) as test_count
        FROM patients ORDER BY patient_name
    """)
    patients = c.fetchall()
    logger.info(f"\nPatients List")
    for p in patients:
        logger.info(f"ID: {p['patient_id']}")
        logger.info(f"Name: {p['patient_name']}")
        logger.info(f"Age: {p['age']} | Gender: {p['gender']}")
        logger.info(f"Test Date: {p['test_date']}")
        logger.info(f"Lab Tests: {p['test_count']}")
        logger.info("-" * 30)

def show_patient_tests(conn, patient_id):
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    patient = c.fetchone()
    if not patient:
        logger.error(f"Patient '{patient_id}' not found")
        return
    logger.info(f"\nLab Tests for: {patient['patient_name']}")
    c.execute("""
        SELECT test_name, test_result, units, reference_range, status
        FROM lab_tests WHERE patient_id = ? ORDER BY test_name
    """, (patient_id,))
    tests = c.fetchall()
    for t in tests:
        logger.info(f"Test: {t['test_name']}")
        logger.info(f"Result: {t['test_result']} {t['units']}")
        if t['reference_range']:
            logger.info(f"Reference: {t['reference_range']}")
        if t['status']:
            logger.info(f"Status: {t['status']}")
        logger.info("-" * 20)

def delete_patient(conn, patient_id):
    c = conn.cursor()
    c.execute("SELECT patient_name FROM patients WHERE patient_id = ?", (patient_id,))
    patient = c.fetchone()
    if not patient:
        logger.error(f"Patient '{patient_id}' not found")
        return
    confirm = input(f"Delete patient '{patient['patient_name']}' and all their tests? (y/N): ")
    if confirm.lower() != 'y':
        logger.warning("Cancelled")
        return
    c.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
    conn.commit()
    logger.info(f"Deleted patient '{patient['patient_name']}'")

def main():
    if len(sys.argv) < 2:
        logger.info("SQLite Inspector Usage:")
        logger.info("  python sqlite_inspector.py stats")
        logger.info("  python sqlite_inspector.py patients")
        logger.info("  python sqlite_inspector.py tests <patient_id>")
        logger.info("  python sqlite_inspector.py delete <patient_id>")
        return
    command = sys.argv[1].lower()
    conn = connect_db()
    if not conn:
        return
    try:
        if command == "stats":
            show_stats(conn)
        elif command == "patients":
            list_patients(conn)
        elif command == "tests":
            if len(sys.argv) < 3:
                logger.error("Please provide patient_id")
                return
            show_patient_tests(conn, sys.argv[2])
        elif command == "delete":
            if len(sys.argv) < 3:
                logger.error("Please provide patient_id")
                return
            delete_patient(conn, sys.argv[2])
        else:
            logger.error(f"Unknown command: {command}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
