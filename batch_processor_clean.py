#!/usr/bin/env python3
"""
Lab Report Batch Processor

A clean, modular system for processing lab report images into structured JSON data.
Uses OpenAI SDK with agent-based approach for reliable extraction and validation.

Usage:
    python batch_processor_clean.py
    
    Processes images from 'lab_images' directory
    Outputs structured JSON to 'processed_reports' directory
"""

import logging
from pathlib import Path

from lab_processor.batch import BatchProcessor

# Simple logging setup
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Main entry point for batch processing."""
    
    # Configuration
    input_directory = "lab_images"
    output_directory = "processed_reports"
    
    print("Lab Report Batch Processor")
    print(f"Input: {input_directory}")
    print(f"Output: {output_directory}")
    
    # Check input directory exists
    if not Path(input_directory).exists():
        print(f"❌ Input directory '{input_directory}' not found")
        print("Please create the directory and add lab report images")
        return
    
    try:
        # Run batch processing
        processor = BatchProcessor()
        results = processor.process_directory(input_directory, output_directory)
        
        # Simple success message
        stats = results['statistics']
        if stats['successful'] > 0:
            print(f"\n✅ Successfully processed {stats['successful']} lab reports")
        if stats['failed'] > 0:
            print(f"⚠️  {stats['failed']} files failed to process")
            
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Processing failed: {e}")
        logging.error(f"Batch processing error: {e}")

if __name__ == "__main__":
    main()
