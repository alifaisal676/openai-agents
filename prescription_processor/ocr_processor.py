"""
📄 OCR Processing Module
Handles text extraction from prescription images using Azure OCR.
"""

import time
import re
import requests
import logging
from langsmith import traceable

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@traceable(run_type="tool", name="azure_ocr_extraction")
def extract_text_from_prescription(image_path, azure_endpoint, azure_key):
    """📄 Extract text from prescription using Azure OCR"""
    logging.info("Reading text from prescription image...")
    
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
    
    request_headers = {
        'Ocp-Apim-Subscription-Key': azure_key,
        'Content-Type': 'application/octet-stream'
    }
    
    # Send to Azure OCR
    ocr_url = f"{azure_endpoint.rstrip('/')}/vision/v3.2/read/analyze"
    ocr_response = requests.post(ocr_url, headers=request_headers, data=image_data)
    
    if ocr_response.status_code != 202:
        logging.error(f"OCR Error: {ocr_response.text}")
        ocr_response.raise_for_status()
    
    operation_url = ocr_response.headers['Operation-Location']
    
    # Wait for processing
    logging.info("Waiting for OCR processing...")
    while True:
        result_response = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': azure_key})
        processing_result = result_response.json()
        
        if processing_result['status'] == 'succeeded':
            logging.info("Text extraction completed!")
            break
        elif processing_result['status'] == 'failed':
            raise Exception("OCR processing failed")
        
        time.sleep(2)
    
    # Extract all text
    extracted_text = ""
    for page in processing_result['analyzeResult']['readResults']:
        for line in page['lines']:
            extracted_text += line['text'] + '\n'
    
    return extracted_text

def clean_extracted_text(raw_text):
    """🧹 Clean up OCR text for better AI processing"""
    logging.info("Cleaning up extracted text...")
    
    # Normalize spacing and remove problematic characters
    cleaned_text = re.sub(r'\n+', ' ', raw_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = re.sub(r'[^\w\s\+\-\.\,\:\;\(\)\[\]\/]', ' ', cleaned_text)
    
    # Standardize medical notation
    cleaned_text = re.sub(r'\s*\+\s*', '+', cleaned_text)
    cleaned_text = re.sub(r'\s*mg\s*', 'mg ', cleaned_text)
    
    logging.info("Text cleaning completed!")
    return cleaned_text.strip()
