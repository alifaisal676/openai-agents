import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class SQLiteLabReportManager:
    def __init__(self, db_path="lab_reports.db"):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
            return False


    def create_tables(self):
        try:
            c = self.connection.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT UNIQUE NOT NULL,
                    patient_name TEXT NOT NULL,
                    age TEXT,
                    gender TEXT,
                    doctor_name TEXT,
                    test_date DATE,
                    lab_name TEXT,
                    comments TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS lab_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    test_result TEXT,
                    units TEXT,
                    reference_range TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
                )
            """)
            self.connection.commit()
            logger.info("Tables created")
            return True
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            return False



    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
        logger.info("SQLite connection closed")




    def get_database_stats(self):
        try:
            c = self.connection.cursor()
            stats = {}
            c.execute("SELECT COUNT(*) FROM patients")
            stats['total_patients'] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM lab_tests")
            stats['total_tests'] = c.fetchone()[0]
            c.execute("SELECT COUNT(DISTINCT test_name) FROM lab_tests")
            stats['unique_test_types'] = c.fetchone()[0]
            db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            stats['database_size_mb'] = round(db_size / (1024 * 1024), 2)
            return stats
        except Exception as e:
            logger.error(f"Stats failed: {e}")
            return {}



    def list_patients(self):
        try:
            c = self.connection.cursor()
            c.execute("SELECT patient_id, patient_name, age, gender, doctor_name, test_date FROM patients ORDER BY created_at DESC")
            return c.fetchall()
        except Exception as e:
            logger.error(f"List patients failed: {e}")
            return []



    def get_patient_tests(self, patient_id):
        try:
            c = self.connection.cursor()
            c.execute("SELECT * FROM lab_tests WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,))
            return c.fetchall()
        except Exception as e:
            logger.error(f"Get patient tests failed: {e}")
            return []



    def delete_patient(self, patient_id):
        try:
            c = self.connection.cursor()
            c.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
            self.connection.commit()
            logger.info(f"Deleted patient: {patient_id}")
            return True
        except Exception as e:
            logger.error(f"Delete patient failed: {e}")
            return False
