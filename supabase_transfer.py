"""
Supabase Database Integration for Lab Report Processing System
Transfers structured JSON lab reports to Supabase using Supabase Python client.

Features:
- Uses Supabase Python client (works with free tier)
- No direct PostgreSQL connection required
- REST API based integration
- Built-in authentication and security
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('supabase_transfer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SupabaseLabReportManager:
    """Manages Supabase operations for lab reports using Supabase Python client."""
    
    def __init__(self):
        """Initialize Supabase client from environment variables."""
        self.supabase: Client = None
        
        # Supabase connection details from environment
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
    def connect(self) -> bool:
        """Establish Supabase client connection."""
        if not self.supabase_url or not self.supabase_key:
            logger.error("❌ Supabase configuration missing. Please set SUPABASE_URL and SUPABASE_ANON_KEY in .env")
            return False
            
        try:
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            logger.info("✅ Successfully connected to Supabase")
            return True
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            return False
    
    def create_tables(self) -> bool:
        """Create the required database tables using Supabase SQL editor or migrations."""
        try:
            # Check if tables exist by trying to select from them
            try:
                self.supabase.table('patients').select('*').limit(1).execute()
                logger.info("📋 Patients table already exists")
            except Exception:
                logger.warning("⚠️  Patients table doesn't exist. Please create it in Supabase SQL editor:")
                print("""
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(100) UNIQUE NOT NULL,
    patient_name VARCHAR(255) NOT NULL,
    age VARCHAR(50),
    gender VARCHAR(20),
    doctor_name VARCHAR(255),
    test_date DATE,
    lab_name VARCHAR(255),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
                """)
            
            try:
                self.supabase.table('lab_tests').select('*').limit(1).execute()
                logger.info("🧪 Lab tests table already exists")
            except Exception:
                logger.warning("⚠️  Lab tests table doesn't exist. Please create it in Supabase SQL editor:")
                print("""
CREATE TABLE IF NOT EXISTS lab_tests (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(100) NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    test_result VARCHAR(255),
    units VARCHAR(50),
    reference_range VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);
                """)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Table verification failed: {e}")
            return False
    
    def insert_patient(self, patient_data: Dict[str, Any]) -> bool:
        """
        Insert patient data with duplicate prevention using Supabase client.
        """
        try:
            # Parse test_date if available
            test_date = None
            if patient_data.get('date'):
                try:
                    # Try different date formats
                    date_str = patient_data['date']
                    for fmt in ['%d %b, %Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            test_date = datetime.strptime(date_str, fmt).date().isoformat()
                            break
                        except ValueError:
                            continue
                except Exception:
                    logger.warning(f"Could not parse date: {patient_data.get('date')}")
            
            # Generate patient_id if not available (fallback)
            patient_id = patient_data.get('patient_id') or patient_data.get('patient_name', 'Unknown').replace(' ', '_')
            
            # Check if patient already exists
            existing_patient = self.supabase.table('patients').select('*').eq('patient_id', patient_id).execute()
            
            if existing_patient.data:
                logger.info(f"👤 Patient already exists: {patient_data.get('patient_name')} (ID: {patient_id})")
                return True
            
            # Insert new patient
            patient_record = {
                'patient_id': patient_id,
                'patient_name': patient_data.get('patient_name', 'Unknown'),
                'age': patient_data.get('age', ''),
                'gender': patient_data.get('gender', ''),
                'doctor_name': patient_data.get('doctor_name', ''),
                'test_date': test_date,
                'lab_name': patient_data.get('lab_name', ''),
                'comments': patient_data.get('comments', '')
            }
            
            result = self.supabase.table('patients').insert(patient_record).execute()
            
            if result.data:
                logger.info(f"👤 New patient inserted: {patient_data.get('patient_name')} (ID: {patient_id})")
                return True
            else:
                logger.error(f"❌ Failed to insert patient: {patient_id}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Patient insertion failed: {e}")
            return False
    
    def insert_tests(self, patient_id: str, test_results: List[Dict[str, Any]]) -> int:
        """
        Insert lab test results for a patient using Supabase client.
        Returns the number of tests successfully inserted.
        """
        inserted_count = 0
        
        try:
            for test in test_results:
                try:
                    test_record = {
                        'patient_id': patient_id,
                        'test_name': test.get('test_name', 'Unknown Test'),
                        'test_result': test.get('value', test.get('result', '')),  # Handle both 'value' and 'result' keys
                        'units': test.get('unit', ''),
                        'reference_range': test.get('reference_range', ''),
                        'status': test.get('status', '')
                    }
                    
                    result = self.supabase.table('lab_tests').insert(test_record).execute()
                    
                    if result.data:
                        inserted_count += 1
                    else:
                        logger.warning(f"⚠️  Failed to insert test {test.get('test_name')}")
                    
                except Exception as e:
                    logger.warning(f"⚠️  Failed to insert test {test.get('test_name')}: {e}")
                    continue
            
            logger.info(f"🧪 Inserted {inserted_count}/{len(test_results)} tests for patient {patient_id}")
            return inserted_count
            
        except Exception as e:
            logger.error(f"❌ Tests insertion failed: {e}")
            return 0
    
    def process_json_file(self, json_file_path: str) -> Dict[str, Any]:
        """
        Process a single JSON lab report file using Supabase client.
        Returns processing statistics.
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                lab_data = json.load(f)
            
            filename = Path(json_file_path).name
            logger.info(f"📄 Processing file: {filename}")
            
            # Extract patient ID (fallback logic)
            patient_id = (lab_data.get('patient_id') or 
                         lab_data.get('patient_name', 'Unknown').replace(' ', '_'))
            
            # Insert patient data
            patient_success = self.insert_patient(lab_data)
            
            # Insert test results
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
            logger.error(f"❌ Failed to process {json_file_path}: {e}")
            return {
                'file': Path(json_file_path).name,
                'status': 'failed',
                'error': str(e)
            }
    
    def batch_process_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Process all JSON files in the specified directory.
        Returns comprehensive processing statistics.
        """
        start_time = datetime.now()
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error(f"❌ Directory not found: {directory_path}")
            return {'error': 'Directory not found'}
        
        # Find all JSON files
        json_files = list(directory.glob('*_structured.json'))
        logger.info(f"🔍 Found {len(json_files)} JSON files to process")
        
        if not json_files:
            logger.warning("⚠️  No structured JSON files found")
            return {'warning': 'No JSON files found'}
        
        # Process each file
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
        
        # Calculate final statistics
        end_time = datetime.now()
        results['statistics']['processing_time'] = (end_time - start_time).total_seconds()
        results['statistics']['successful_files'] = len(results['successful'])
        results['statistics']['failed_files'] = len(results['failed'])
        results['statistics']['total_patients'] = len(set(
            r['patient_id'] for r in results['successful']
        ))
        
        return results
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get current database statistics using Supabase client."""
        try:
            stats = {}
            
            # Count patients
            patients_result = self.supabase.table('patients').select('*', count='exact').execute()
            stats['total_patients'] = patients_result.count or 0
            
            # Count tests
            tests_result = self.supabase.table('lab_tests').select('*', count='exact').execute()
            stats['total_tests'] = tests_result.count or 0
            
            # Count unique test types
            unique_tests_result = self.supabase.table('lab_tests').select('test_name').execute()
            unique_test_names = set(test['test_name'] for test in unique_tests_result.data)
            stats['unique_test_types'] = len(unique_test_names)
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get database stats: {e}")
            return {}
    
    def close(self):
        """Close Supabase client connections."""
        if self.supabase:
            # Supabase client doesn't need explicit closing
            self.supabase = None
        logger.info("🔌 Supabase client disconnected")

def main():
    """Main function to execute the Supabase database transfer process."""
    
    # Configuration
    json_directory = "processed_reports"
    
    print("\n" + "="*70)
    print("🚀 LAB REPORTS → SUPABASE DATABASE TRANSFER")
    print("="*70)
    print(f"📁 Source Directory: {json_directory}")
    print(f"☁️  Target: Supabase PostgreSQL")
    print("="*70)
    
    # Initialize Supabase database manager
    db_manager = SupabaseLabReportManager()
    
    # Check if Supabase is configured
    if not db_manager.supabase_url or not db_manager.supabase_key:
        print("❌ Supabase not configured!")
        print("💡 Please set up your .env file with:")
        print("   SUPABASE_URL=https://your-project.supabase.co")
        print("   SUPABASE_ANON_KEY=your_anon_key")
        return
    
    try:
        # Connect to Supabase
        if not db_manager.connect():
            print("❌ Failed to connect to Supabase. Please check your configuration.")
            return
        
        # Create tables
        if not db_manager.create_tables():
            print("❌ Failed to create database tables.")
            return
        
        # Get initial database stats
        initial_stats = db_manager.get_database_stats()
        logger.info(f"📊 Initial Supabase Stats: {initial_stats}")
        
        # Process all JSON files
        results = db_manager.batch_process_directory(json_directory)
        
        if 'error' in results:
            print(f"❌ Error: {results['error']}")
            return
        
        if 'warning' in results:
            print(f"⚠️  Warning: {results['warning']}")
            return
        
        # Get final database stats
        final_stats = db_manager.get_database_stats()
        
        # Print comprehensive summary
        stats = results['statistics']
        print(f"\n📊 TRANSFER RESULTS")
        print("="*50)
        print(f"📄 Files Processed: {stats['successful_files']}/{stats['total_files']}")
        print(f"👤 Patients: {stats['total_patients']} unique")
        print(f"🧪 Tests Transferred: {stats['total_tests']}")
        print(f"⏱️  Processing Time: {stats['processing_time']:.2f}s")
        
        print(f"\n☁️  SUPABASE DATABASE SUMMARY")
        print("="*50)
        print(f"👥 Total Patients in DB: {final_stats.get('total_patients', 'N/A')}")
        print(f"🧪 Total Tests in DB: {final_stats.get('total_tests', 'N/A')}")
        print(f"📋 Unique Test Types: {final_stats.get('unique_test_types', 'N/A')}")
        
        if results['successful']:
            print(f"\n✅ Successfully Processed Files:")
            for result in results['successful']:
                print(f"  - {result['file']}: {result['patient_name']} ({result['tests_inserted']} tests)")
        
        if results['failed']:
            print(f"\n❌ Failed Files:")
            for result in results['failed']:
                print(f"  - {result['file']}: {result.get('error', 'Unknown error')}")
        
        print("="*70)
        print("✅ Supabase transfer completed successfully!")
        print("🌐 View your data at: https://app.supabase.com/project/your-project/editor")
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        print(f"❌ Transfer failed: {e}")
    
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()
