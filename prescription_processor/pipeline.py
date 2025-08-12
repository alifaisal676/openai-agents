"""
🏥 Main Pipeline Module
Orchestrates the complete prescription processing workflow.
"""

import os
import json
import logging
from dotenv import load_dotenv
from .image_processor import enhance_prescription_image
from .ocr_processor import extract_text_from_prescription, clean_extracted_text
from .llama_extractor import extract_medicines_with_llm
from .database_utils import load_trusted_medicine_database, cross_reference_with_known_medicines

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_prescription(image_path):
    """🏥 Main pipeline: Process prescription image with LLaMA extraction and validation"""
    
    try:
        # Load environment variables
        load_dotenv()
        azure_endpoint = os.getenv('AZURE_OCR_ENDPOINT')
        azure_key = os.getenv('AZURE_OCR_KEY')
        groq_api_key = os.getenv('GROQ_API_KEY')
        
        if not all([azure_endpoint, azure_key, groq_api_key]):
            logging.error("Missing environment variables: need AZURE_OCR_ENDPOINT, AZURE_OCR_KEY, GROQ_API_KEY")
            return []
        
        logging.info("Processing prescription with LLaMA pipeline...")
        os.makedirs("outputs", exist_ok=True)
        
        # Pipeline steps
        logging.info("1. Enhancing image quality...")
        enhanced_image_path = enhance_prescription_image(image_path)
        
        logging.info("2. Extracting text with Azure OCR...")
        raw_prescription_text = extract_text_from_prescription(enhanced_image_path, azure_endpoint, azure_key)
        with open("outputs/ocr_raw.txt", 'w', encoding='utf-8') as f:
            f.write(raw_prescription_text)
        
        logging.info("3. Cleaning text...")
        cleaned_prescription_text = clean_extracted_text(raw_prescription_text)
        with open("outputs/ocr_cleaned.txt", 'w', encoding='utf-8') as f:
            f.write(cleaned_prescription_text)
        logging.info(f"Cleaned text preview: {cleaned_prescription_text[:100]}...")
        
        logging.info("4. Extracting and validating medicines with LLaMA...")
        extracted_medicines = extract_medicines_with_llm(cleaned_prescription_text, groq_api_key, 'https://api.groq.com/openai/v1')
        
        logging.info("5. Cross-checking with medicine database...")
        known_medicine_names = load_trusted_medicine_database("medicines_pk.js")
        final_validated_medicines = cross_reference_with_known_medicines(extracted_medicines, known_medicine_names)
        with open("outputs/step4_final_with_database.json", 'w', encoding='utf-8') as f:
            json.dump(final_validated_medicines, f, indent=2, ensure_ascii=False)
        
        # Cleanup
        if enhanced_image_path != image_path and os.path.exists(enhanced_image_path):
            os.remove(enhanced_image_path)
        
        logging.info("Pipeline completed successfully!")
        logging.info(f"Found {len(final_validated_medicines)} validated medicines:")
        for medicine in final_validated_medicines:
            logging.info(f"Medicine: {medicine['medicine']} | {medicine.get('dosage', 'No dosage')} | {medicine.get('frequency', 'No frequency')} | Confidence: {medicine.get('confidence', 0):.1f}%")
        
        return final_validated_medicines
        
    except Exception as e:
        logging.error(f"Pipeline error: {e}")
        return []
