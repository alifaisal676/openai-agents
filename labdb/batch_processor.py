import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self, processor):
        self.processor = processor
        

    def _find_json_files(self, directory_path):
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory not found: {directory_path}")
            return None
        json_files = list(directory.glob('*_structured.json'))
        logger.info(f"Found {len(json_files)} JSON files to process")
        return json_files


    def _calculate_batch_stats(self, results, start_time, end_time, total_files):
        return {
            'total_files': total_files,
            'total_patients': len(set(r['patient_id'] for r in results['successful'])),
            'total_tests': sum(r['tests_inserted'] for r in results['successful']),
            'processing_time': (end_time - start_time).total_seconds(),
            'successful_files': len(results['successful']),
            'failed_files': len(results['failed'])
        }


    def batch_process_directory(self, directory_path):
        start_time = datetime.now()
        json_files = self._find_json_files(directory_path)
        if json_files is None:
            return {'error': 'Directory not found'}
        if not json_files:
            logger.warning("No structured JSON files found")
            return {'warning': 'No JSON files found'}
        results = {'successful': [], 'failed': []}
        for json_file in json_files:
            result = self.processor.process_json_file(str(json_file))
            if result['status'] == 'success':
                results['successful'].append(result)
            else:
                results['failed'].append(result)
        end_time = datetime.now()
        results['statistics'] = self._calculate_batch_stats(results, start_time, end_time, len(json_files))
        return results



    # Inspector features
    def list_patients(self):
        return self.processor.db_manager.list_patients()

    def get_patient_tests(self, patient_id):
        return self.processor.db_manager.get_patient_tests(patient_id)

    def delete_patient(self, patient_id):
        return self.processor.db_manager.delete_patient(patient_id)
