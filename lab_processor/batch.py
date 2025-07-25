"""
Batch processor for multiple lab reports.
"""
import json
import time
import logging
from pathlib import Path

from .agent import LabReportAgent
from .utils import find_lab_images, is_already_processed, setup_output_directory, get_output_filename

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Processes multiple lab report images."""
    
    def __init__(self):
        self.agent = LabReportAgent()
        self.results = {
            'successful': [],
            'failed': [],
            'skipped': []
        }
    
    def process_directory(self, input_dir: str, output_dir: str) -> dict:
        """Process all lab images in directory."""
        start_time = time.time()
        
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        setup_output_directory(output_path)
        images = find_lab_images(input_path)
        
        print(f"\nFound {len(images)} images to process")
        print("-" * 50)
        
        for i, image_path in enumerate(images, 1):
            print(f"Processing {i}/{len(images)}: {image_path.name}")
            
            if is_already_processed(image_path, output_path):
                self._add_skipped_result(image_path, output_path)
                print("  → Skipped (already done)")
                continue
            
            output_file = get_output_filename(image_path, output_path)
            result = self.agent.process_image(str(image_path), str(output_file))
            
            self._categorize_result(result)
            self._print_result(result)
        
        return self._create_summary(len(images), time.time() - start_time, output_path)
    
    def _add_skipped_result(self, image_path: Path, output_path: Path):
        """Add skipped file to results."""
        self.results['skipped'].append({
            'image': image_path.name,
            'reason': 'already_processed',
            'output_file': f"{image_path.stem}_structured.json"
        })
    
    def _categorize_result(self, result: dict):
        """Sort result into appropriate category."""
        if result['status'] == 'success':
            self.results['successful'].append(result)
        else:
            self.results['failed'].append(result)
    
    def _print_result(self, result: dict):
        """Print processing result."""
        if result['status'] == 'success':
            print(f"  ✅ {result['patient_name']} ({result['duration']:.1f}s)")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown')} ({result['duration']:.1f}s)")
    
    def _create_summary(self, total_images: int, duration: float, output_path: Path) -> dict:
        """Create processing summary."""
        successful = len(self.results['successful'])
        failed = len(self.results['failed'])
        skipped = len(self.results['skipped'])
        processed = successful + failed
        
        summary = {
            'statistics': {
                'total_images': total_images,
                'successful': successful,
                'failed': failed,
                'skipped': skipped,
                'processed': processed,
                'duration': f"{duration:.1f}s",
                'avg_per_image': f"{duration/max(processed, 1):.1f}s"
            },
            'results': self.results
        }
        
        # Save summary
        summary_file = output_path / "processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self._print_summary(summary['statistics'])
        return summary
    
    def _print_summary(self, stats: dict):
        """Print final processing summary."""
        print("\n" + "="*50)
        print("PROCESSING SUMMARY")
        print("="*50)
        print(f"Total Images: {stats['total_images']}")
        print(f"✅ Successful: {stats['successful']}")
        print(f"⏭️  Skipped: {stats['skipped']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"⏱️  Duration: {stats['duration']}")
        print(f"📊 Avg/Image: {stats['avg_per_image']}")
        print("="*50)
