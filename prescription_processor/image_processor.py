"""
🖼️ Image Processing Module
Handles prescription image enhancement for better OCR results.
"""

import cv2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def enhance_prescription_image(image_path):
    """🖼️ Enhance image quality for better OCR results"""
    try:
        logging.info("Loading and enhancing image...")
        
        prescription_image = cv2.imread(image_path)
        grayscale_image = cv2.cvtColor(prescription_image, cv2.COLOR_BGR2GRAY)
        clean_image = cv2.fastNlMeansDenoising(grayscale_image)
        
        # Enhance contrast for clearer text
        contrast_enhancer = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced_image = contrast_enhancer.apply(clean_image)
        
        enhanced_image_path = "temp_enhanced_prescription.png"
        cv2.imwrite(enhanced_image_path, enhanced_image)
        
        logging.info("Image enhancement completed!")
        return enhanced_image_path
        
    except Exception as error:
        logging.warning(f"Image enhancement failed: {error}")
        logging.info("Using original image instead...")
        return image_path
