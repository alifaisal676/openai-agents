

import logging
from pathlib import Path

from labdb.db_manager import SQLiteLabReportManager
from labdb.lab_report_processor import LabReportProcessor
from labdb.batch_processor import BatchProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)





import sys
def main():
    json_directory = "processed_reports"
    database_file = str(Path("labdb") / "lab_reports.db")
    logger.info("\n" + "="*60)
    logger.info("Lab Reports → SQLite Database Transfer")
    logger.info("="*60)
    logger.info(f"Source Directory: {json_directory}")
    logger.info(f"Target Database: {database_file}")
    logger.info("="*60)
    db_manager = SQLiteLabReportManager(database_file)
    processor = LabReportProcessor(db_manager)
    batcher = BatchProcessor(processor)
    try:
        if not db_manager.connect():
            logger.error("Failed to connect to SQLite database.")
            return
        if not db_manager.create_tables():
            logger.error("Failed to create database tables.")
            return

        # Inspector CLI features
        if len(sys.argv) > 1:
            cmd = sys.argv[1].lower()
            if cmd == "list":
                patients = batcher.list_patients()
                logger.info("\nPatients in database:")
                for p in patients:
                    logger.info(f"- {p['patient_id']}: {p['patient_name']} | Age: {p['age']} | Gender: {p['gender']} | Doctor: {p['doctor_name']} | Date: {p['test_date']}")
                return
            elif cmd == "tests" and len(sys.argv) > 2:
                patient_id = sys.argv[2]
                tests = batcher.get_patient_tests(patient_id)
                logger.info(f"\nTests for patient {patient_id}:")
                for t in tests:
                    logger.info(f"- {t['test_name']}: {t['test_result']} {t['units']} (Ref: {t['reference_range']}) Status: {t['status']}")
                return
            elif cmd == "delete" and len(sys.argv) > 2:
                patient_id = sys.argv[2]
                if batcher.delete_patient(patient_id):
                    logger.info(f"Deleted patient: {patient_id}")
                else:
                    logger.warning(f"Failed to delete patient: {patient_id}")
                return



        # Default: batch process
        initial_stats = db_manager.get_database_stats()
        logger.info(f"Initial SQLite Stats: {initial_stats}")
        results = batcher.batch_process_directory(json_directory)
        if 'error' in results:
            logger.error(f"Error: {results['error']}")
            return
        if 'warning' in results:
            logger.warning(f"Warning: {results['warning']}")
            return
        final_stats = db_manager.get_database_stats()
        stats = results['statistics']
        logger.info("\nTransfer Results")
        logger.info("-"*40)
        logger.info(f"Files Processed: {stats['successful_files']}/{stats['total_files']}")
        logger.info(f"Unique Patients: {stats['total_patients']}")
        logger.info(f"Tests Transferred: {stats['total_tests']}")
        logger.info(f"Processing Time: {stats['processing_time']:.2f}s")
        logger.info("\nSQLite Database Summary")
        logger.info("-"*40)
        
        
        
        logger.info(f"Total Patients: {final_stats.get('total_patients', 'N/A')}")
        logger.info(f"Total Tests: {final_stats.get('total_tests', 'N/A')}")
        logger.info(f"Unique Test Types: {final_stats.get('unique_test_types', 'N/A')}")
        logger.info(f"Database Size: {final_stats.get('database_size_mb', 'N/A')} MB")
        if results['successful']:
            logger.info("\nSuccessfully Processed Files:")
            for result in results['successful']:
                logger.info(f"  - {result['file']}: {result['patient_name']} ({result['tests_inserted']} tests)")
        if results['failed']:
            logger.warning("\nFailed Files:")
            for result in results['failed']:
                logger.warning(f"  - {result['file']}: {result.get('error', 'Unknown error')}")
        logger.info("="*60)
        logger.info("SQLite transfer completed.")
        logger.info(f"Database location: {Path(database_file).absolute()}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error("Transfer failed.")
    finally:
        db_manager.close()


if __name__ == "__main__":
    main()
