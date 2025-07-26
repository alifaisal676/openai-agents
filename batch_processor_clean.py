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
   
    
    # Configuration
    input_directory = "lab_images"
    output_directory = "processed_reports"
    
    logger.info("Starting batch processing of lab reports...")
    logger.info(f"Looking for images in: {input_directory}")
    logger.info(f"Processed reports will be saved to: {output_directory}")

    if not Path(input_directory).exists():
        logger.error(f"Input folder '{input_directory}' does not exist.")
        logger.error("Please create it and add your lab report images before running this script.")
        return

    try:
        processor = BatchProcessor()
        results = processor.process_directory(input_directory, output_directory)
        stats = results['statistics']
        if stats['successful'] > 0:
            logger.info(f"All done! {stats['successful']} lab reports processed successfully.")
        if stats['failed'] > 0:
            logger.warning(f"{stats['failed']} files could not be processed. Please check the logs above for details.")
    except KeyboardInterrupt:
        logger.warning("Batch processing stopped by user.")
    except Exception as e:
        logger.error(f"Something went wrong: {e}")
        logging.error(f"Batch processing error: {e}")

if __name__ == "__main__":
    main()
