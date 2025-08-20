import json
import logging
from prescription_processor import process_prescription

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """🏥 Main function to run the prescription processing pipeline"""
    result = process_prescription(image_path="pics/pic.jpg")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    main()
