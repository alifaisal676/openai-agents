
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('sqlite_transfer.log', encoding='utf-8'), logging.StreamHandler()]
)
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

    def insert_patient(self, patient_data):
        try:
            c = self.connection.cursor()
            test_date = None
            if patient_data.get('date'):
                for fmt in ['%d %b, %Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                    try:
                        test_date = datetime.strptime(patient_data['date'], fmt).date().isoformat()
                        break
                    except ValueError:
                        continue
            patient_id = patient_data.get('patient_id') or patient_data.get('patient_name', 'Unknown').replace(' ', '_')
            c.execute("SELECT COUNT(*) FROM patients WHERE patient_id = ?", (patient_id,))
            if c.fetchone()[0] > 0:
                logger.info(f"Patient exists: {patient_data.get('patient_name')} ({patient_id})")
                return True
            c.execute("""
                INSERT INTO patients (patient_id, patient_name, age, gender, doctor_name, test_date, lab_name, comments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id,
                patient_data.get('patient_name', 'Unknown'),
                patient_data.get('age', ''),
                patient_data.get('gender', ''),
                patient_data.get('doctor_name', ''),
                test_date,
                patient_data.get('lab_name', ''),
                patient_data.get('comments', '')
            ))
            self.connection.commit()
            logger.info(f"Inserted patient: {patient_data.get('patient_name')} ({patient_id})")
            return True
        except Exception as e:
            logger.error(f"Patient insert failed: {e}")
            return False

    def insert_tests(self, patient_id, test_results):
        count = 0
        try:
            c = self.connection.cursor()
            c.execute("SELECT test_name FROM lab_tests WHERE patient_id = ?", (patient_id,))
            existing = set(row[0].strip().lower() for row in c.fetchall() if row[0])
            for test in test_results:
                name = (test.get('test_name', 'Unknown Test') or '').strip().lower()
                if name in existing:
                    logger.info(f"Skip duplicate test '{test.get('test_name')}' for {patient_id}")
                    continue
                try:
                    c.execute("""
                        INSERT INTO lab_tests (patient_id, test_name, test_result, units, reference_range, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        patient_id,
                        test.get('test_name', 'Unknown Test'),
                        test.get('value', test.get('result', '')),
                        test.get('unit', ''),
                        test.get('reference_range', ''),
                        test.get('status', '')
                    ))
                    count += 1
                    existing.add(name)
                except Exception as e:
                    logger.warning(f"Test insert failed: {test.get('test_name')}: {e}")
                    continue
            self.connection.commit()
            logger.info(f"Inserted {count}/{len(test_results)} new tests for {patient_id}")
            return count
        except Exception as e:
            logger.error(f"Test insert failed: {e}")
            return 0

    def delete_patient(self, patient_id):
        try:
            c = self.connection.cursor()
            c.execute("SELECT COUNT(*) FROM patients WHERE patient_id = ?", (patient_id,))
            if c.fetchone()[0] == 0:
                logger.warning(f"No patient found: {patient_id}")
                return False
            c.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
            self.connection.commit()
            logger.info(f"Deleted patient: {patient_id}")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def process_json_file(self, json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                lab_data = json.load(f)
            filename = Path(json_file_path).name
            logger.info(f"Processing file: {filename}")
            patient_id = lab_data.get('patient_id') or lab_data.get('patient_name', 'Unknown').replace(' ', '_')
            patient_success = self.insert_patient(lab_data)
            test_results = lab_data.get('test_results', [])
            tests_inserted = self.insert_tests(patient_id, test_results)
            return {
                'file': filename,
                'status': 'success',
                'patient_id': patient_id,
                'patient_name': lab_data.get('patient_name', 'Unknown'),
                'tests_count': len(test_results),
                'tests_inserted': tests_inserted,
                'patient_inserted': patient_success
            }
        except Exception as e:
            logger.error(f"Process failed: {json_file_path}: {e}")
            return {
                'file': Path(json_file_path).name,
                'status': 'failed',
                'error': str(e)
            }

    def batch_process_directory(self, directory_path):
        start_time = datetime.now()
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory not found: {directory_path}")
            return {'error': 'Directory not found'}
        json_files = list(directory.glob('*_structured.json'))
        logger.info(f"Found {len(json_files)} JSON files to process")
        if not json_files:
            logger.warning("No structured JSON files found")
            return {'warning': 'No JSON files found'}
        results = {
            'successful': [],
            'failed': [],
            'statistics': {
                'total_files': len(json_files),
                'total_patients': 0,
                'total_tests': 0,
                'processing_time': 0
            }
        }
        for json_file in json_files:
            result = self.process_json_file(str(json_file))
            if result['status'] == 'success':
                results['successful'].append(result)
                results['statistics']['total_tests'] += result['tests_inserted']
            else:
                results['failed'].append(result)
        end_time = datetime.now()
        results['statistics']['processing_time'] = (end_time - start_time).total_seconds()
        results['statistics']['successful_files'] = len(results['successful'])
        results['statistics']['failed_files'] = len(results['failed'])
        results['statistics']['total_patients'] = len(set(r['patient_id'] for r in results['successful']))
        return results

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

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
        logger.info("SQLite connection closed")

def main():
    json_directory = "processed_reports"
    database_file = "lab_reports.db"
    logger.info("\n" + "="*60)
    logger.info("Lab Reports → SQLite Database Transfer")
    logger.info("="*60)
    logger.info(f"Source Directory: {json_directory}")
    logger.info(f"Target Database: {database_file}")
    logger.info("="*60)
    db_manager = SQLiteLabReportManager(database_file)
    try:
        if not db_manager.connect():
            logger.error("Failed to connect to SQLite database.")
            return
        if not db_manager.create_tables():
            logger.error("Failed to create database tables.")
            return
        initial_stats = db_manager.get_database_stats()
        logger.info(f"Initial SQLite Stats: {initial_stats}")
        results = db_manager.batch_process_directory(json_directory)
        if 'error' in results:
            logger.error(f"Error: {results['error']}")
            return
        if 'warning' in results:
            logger.warning(f"Warning: {results['warning']}")
            return
        final_stats = db_manager.get_database_stats()
        stats = results['statistics']
        logger.info(f"\nTransfer Results")
        logger.info("-"*40)
        logger.info(f"Files Processed: {stats['successful_files']}/{stats['total_files']}")
        logger.info(f"Patients: {stats['total_patients']} unique")
        logger.info(f"Tests Transferred: {stats['total_tests']}")
        logger.info(f"Processing Time: {stats['processing_time']:.2f}s")
        logger.info(f"\nSQLite Database Summary")
        logger.info("-"*40)
        logger.info(f"Total Patients: {final_stats.get('total_patients', 'N/A')}")
        logger.info(f"Total Tests: {final_stats.get('total_tests', 'N/A')}")
        logger.info(f"Unique Test Types: {final_stats.get('unique_test_types', 'N/A')}")
        logger.info(f"Database Size: {final_stats.get('database_size_mb', 'N/A')} MB")
        if results['successful']:
            logger.info(f"\nSuccessfully Processed Files:")
            for result in results['successful']:
                logger.info(f"  - {result['file']}: {result['patient_name']} ({result['tests_inserted']} tests)")
        if results['failed']:
            logger.warning(f"\nFailed Files:")
            for result in results['failed']:
                logger.warning(f"  - {result['file']}: {result.get('error', 'Unknown error')}")
        logger.info("="*60)
        logger.info("SQLite transfer completed.")
        logger.info(f"Database location: {Path(database_file).absolute()}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Transfer failed: {e}")
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()
