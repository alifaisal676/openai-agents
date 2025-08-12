#!/usr/bin/env python3
"""
🏥 Prescription Processor - Main Entry Point

Smart prescription reader that extracts medicine information from images.
Uses Azure OCR + LLaMA AI for extraction and validation against medicine database.
"""

import json
import logging
from prescription_processor import process_prescription

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """🏥 Main function to run the prescription processing pipeline"""
    result = process_prescription(image_path="pics/pic3.jpeg")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    main()
