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
logger = logging.getLogger(__name__)

def main():
    """Main entry point for batch processing."""
    
    # Configuration
    input_directory = "lab_images"
    output_directory = "processed_reports"
    
    logger.info("Lab Report Batch Processor")
    logger.info(f"Input: {input_directory}")
    logger.info(f"Output: {output_directory}")

    # Check input directory exists
    if not Path(input_directory).exists():
        logger.error(f"❌ Input directory '{input_directory}' not found")
        logger.error("Please create the directory and add lab report images")
        return

    try:
        # Run batch processing
        processor = BatchProcessor()
        results = processor.process_directory(input_directory, output_directory)

        # Simple success message
        stats = results['statistics']
        if stats['successful'] > 0:
            logger.info(f"\n✅ Successfully processed {stats['successful']} lab reports")
        if stats['failed'] > 0:
            logger.warning(f"⚠️  {stats['failed']} files failed to process")

    except KeyboardInterrupt:
        logger.warning("\n⏹️  Processing interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Processing failed: {e}")
        logging.error(f"Batch processing error: {e}")

if __name__ == "__main__":
    main()
