import logging
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class LabReportProcessor:
    
    def __init__(self, db_manager):
        self.db_manager = db_manager



    def insert_patient(self, patient):
       
        try:
            c = self.db_manager.connection.cursor()
            # Try to parse the date in a flexible way
            test_date = None
            if patient.get('date'):
                for fmt in ['%d %b, %Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                    try:
                        test_date = datetime.strptime(patient['date'], fmt).date().isoformat()
                        break
                    except ValueError:
                        continue
            patient_id = patient.get('patient_id') or patient.get('patient_name', 'Unknown').replace(' ', '_')
            c.execute("SELECT COUNT(*) FROM patients WHERE patient_id = ?", (patient_id,))
            if c.fetchone()[0] > 0:
                logger.info(f"Patient already exists: {patient.get('patient_name')} ({patient_id})")
                return True
            c.execute(
                """
                INSERT INTO patients (patient_id, patient_name, age, gender, doctor_name, test_date, lab_name, comments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient_id,
                    patient.get('patient_name', 'Unknown'),
                    patient.get('age', ''),
                    patient.get('gender', ''),
                    patient.get('doctor_name', ''),
                    test_date,
                    patient.get('lab_name', ''),
                    patient.get('comments', '')
                )
            )
            self.db_manager.connection.commit()
            logger.info(f"Added patient: {patient.get('patient_name')} ({patient_id})")
            return True
        except Exception as e:
            logger.error(f"Could not insert patient: {e}")
            return False
        
        
        

    def insert_tests(self, patient_id, test_results):
        count = 0
        try:
            c = self.db_manager.connection.cursor()
            c.execute("SELECT test_name FROM lab_tests WHERE patient_id = ?", (patient_id,))
            existing = set(row[0].strip().lower() for row in c.fetchall() if row[0])
            for test in test_results:
                name = (test.get('test_name', 'Unknown Test') or '').strip().lower()
                if name in existing:
                    logger.info(f"Duplicate test skipped: '{test.get('test_name')}' for {patient_id}")
                    continue
                try:
                    c.execute(
                        """
                        INSERT INTO lab_tests (patient_id, test_name, test_result, units, reference_range, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            patient_id,
                            test.get('test_name', 'Unknown Test'),
                            test.get('value', test.get('result', '')),
                            test.get('unit', ''),
                            test.get('reference_range', ''),
                            test.get('status', '')
                        )
                    )
                    count += 1
                    existing.add(name)
                except Exception as e:
                    logger.warning(f"Could not insert test '{test.get('test_name')}': {e}")
                    continue
            self.db_manager.connection.commit()
            logger.info(f"Inserted {count} new tests for {patient_id}")
            return count
        except Exception as e:
            logger.error(f"Test insertion failed: {e}")
            return 0




    def process_json_file(self, json_file_path):
       
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                lab_data = json.load(f)
            filename = Path(json_file_path).name
            logger.info(f"Processing: {filename}")
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
            logger.error(f"Failed to process {json_file_path}: {e}")
            return {
                'file': Path(json_file_path).name,
                'status': 'failed',
                'error': str(e)
            }
