"""
🤖 LLaMA Medicine Extraction Module
Handles AI-powered medicine extraction from prescription text.
"""

import json
import re
from openai import OpenAI
import logging

def ask_llama_to_extract_medicines(prescription_text, groq_api_key, groq_endpoint):
    """🤖 Send prescription text to LLaMA for medicine extraction"""
    try:
        logging.info("Asking LLaMA AI to analyze the prescription...")
        
        ai_client = OpenAI(api_key=groq_api_key, base_url=groq_endpoint)
        
        ai_response = ai_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a medical prescription analyzer. Return only valid JSON arrays with no additional text, explanations, or notes."},
                {"role": "user", "content": prescription_text}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        logging.info("LLaMA AI analysis completed!")
        return ai_response.choices[0].message.content
        
    except Exception as error:
        logging.error(f"LLaMA AI analysis failed: {error}")
        return ""

def extract_medicines_with_llm(text, groq_key, groq_endpoint):
    """Extract medicines using LLaMA with medicine database context"""
    
    logging.info("Using LLaMA for medicine extraction with database context...")
    
    # Load medicine database for context
    try:
        from .database_utils import load_trusted_medicine_database
        medicine_database = load_trusted_medicine_database("medicines_pk.js")
        sample_medicines = medicine_database[:100]  # First 100 medicines as examples
        medicine_context = ", ".join(sample_medicines)
    except:
        medicine_context = "Amoxicillin, Aspirin, Metformin, Paracetamol, Ibuprofen"  # Fallback
    
    # Step 1: Extract medicines using LLaMA with database context
    extraction_prompt = f'''Analyze this prescription text and extract all medicines with their dosages and frequencies.

Prescription text: "{text}"

MEDICINE DATABASE CONTEXT: 
Here are examples of valid medicines from our database: {medicine_context}...

EXTRACTION STRATEGY:
1. First identify all potential pharmaceutical terms (ignore obvious patient/doctor names)
2. Look for patterns like: "word + dosage" (e.g., "Mylène 4mg", "Tras 4mg")  
3. Consider partial names that might be truncated by OCR
4. Extract ALL possible medicine candidates, even if uncertain

SPECIAL INSTRUCTIONS:
- Extract "Mylène" if it appears with dosage - could be a medicine name
- Extract "Tras" if it appears with dosage - could be truncated medicine name
- Look for ANY word followed by mg, ml, tablets, etc.
- Include brand names, generic names, and abbreviated names

IMPORTANT: Return ONLY valid JSON in this exact format with no additional text or explanations:
[
  {{
    "medicine": "medicine_name",
    "dosage": "amount_and_unit", 
    "frequency": "how_often_taken"
  }}
]

Rules:
- If frequency is unclear, use "unknown" not explanatory text
- No parenthetical notes or explanations inside JSON
- No text before or after the JSON array
- If no medicines found, return []

JSON ONLY:'''
    
    llama_response = ask_llama_to_extract_medicines(extraction_prompt, groq_key, groq_endpoint)
    
    # Save extraction response for debugging
    with open("outputs/llama_extraction_response.txt", 'w', encoding='utf-8') as f:
        f.write(f"EXTRACTION PROMPT:\n{extraction_prompt}\n\n")
        f.write(f"LLAMA RESPONSE:\n{llama_response}")
    
    try:
        # Parse the extraction response with improved error handling
        extracted_medicines = []
        
        # First try to find JSON array pattern - be more aggressive
        json_patterns = [
            r'\[.*?\]',  # Standard array
            r'\[\s*\{[^}]*\}\s*\]',  # Simple object in array
            r'\[\s*\{[^}]*"medicine"[^}]*\}[^]]*\]'  # Object with medicine field
        ]
        
        json_text = None
        for pattern in json_patterns:
            json_match = re.search(pattern, llama_response, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                break
        
        if not json_text:
            json_text = llama_response.strip()
        
        # Clean up the JSON more aggressively
        logging.info(f"Raw JSON found: {json_text[:150]}...")
        
        # Remove any text after closing bracket
        json_text = re.sub(r'\]\s*\([^)]*\).*$', ']', json_text, flags=re.DOTALL)
        json_text = re.sub(r'\]\s*Note:.*$', ']', json_text, flags=re.DOTALL)
        json_text = re.sub(r'\}\s*\([^)]*\)', '}', json_text, flags=re.DOTALL)
        
        # Try multiple parsing approaches
        try:
            extracted_medicines = json.loads(json_text)
            logging.info("JSON parsing succeeded")
        except json.JSONDecodeError as e:
            logging.warning(f"Initial JSON parsing failed: {e}")
            
            # Try to clean up common JSON issues
            cleaned_json = json_text.replace("'", '"')  # Replace single quotes
            cleaned_json = re.sub(r',\s*}', '}', cleaned_json)  # Remove trailing commas
            cleaned_json = re.sub(r',\s*]', ']', cleaned_json)  # Remove trailing commas
            cleaned_json = re.sub(r'"\s*\([^)]*\)', '"', cleaned_json)  # Remove parenthetical notes
            
            try:
                extracted_medicines = json.loads(cleaned_json)
                logging.info("JSON parsing succeeded after cleanup")
            except json.JSONDecodeError as e2:
                logging.error(f"JSON parsing failed even after cleanup: {e2}")
                logging.info(f"Cleaned JSON: {cleaned_json[:200]}...")
                
                # Last resort: try to extract individual medicine data manually
                medicine_matches = re.findall(r'"medicine":\s*"([^"]*)"', llama_response)
                dosage_matches = re.findall(r'"dosage":\s*"([^"]*)"', llama_response)
                frequency_matches = re.findall(r'"frequency":\s*"([^"]*)"', llama_response)
                
                if medicine_matches:
                    logging.info(f"Manual extraction found medicines: {medicine_matches}")
                    extracted_medicines = []
                    for i, med in enumerate(medicine_matches):
                        medicine_obj = {"medicine": med}
                        if i < len(dosage_matches):
                            medicine_obj["dosage"] = dosage_matches[i]
                        if i < len(frequency_matches):
                            medicine_obj["frequency"] = frequency_matches[i]
                        extracted_medicines.append(medicine_obj)
                    logging.info("Manual extraction succeeded")
                else:
                    return []
        
        if not isinstance(extracted_medicines, list):
            extracted_medicines = []
            
        logging.info(f"LLaMA extracted {len(extracted_medicines)} medicines: {[m.get('medicine', '') for m in extracted_medicines]}")
        
        # Save extracted medicines
        with open("outputs/step1_extracted_medicines.json", 'w', encoding='utf-8') as f:
            json.dump(extracted_medicines, f, indent=2, ensure_ascii=False)
        
        if not extracted_medicines:
            return []
        
        # Step 2: Validate the extracted medicines with LLM
        from .medicine_validator import smart_medicine_validation
        validated_medicines = smart_medicine_validation(extracted_medicines, groq_key, groq_endpoint)
        
        # Save validation response
        with open("outputs/step2_validation_response.json", 'w', encoding='utf-8') as f:
            json.dump(validated_medicines, f, indent=2, ensure_ascii=False)
        
        # Step 3: Filter only valid medicines (balanced threshold)
        final_medicines = []
        for validated_med in validated_medicines:
            if (validated_med.get('is_valid_medicine', False) and 
                validated_med.get('confidence', 0) >= 0.7):  # Changed to >= to include 0.7
                
                medicine_name = validated_med.get('medicine')
                
                # Find the original medicine data for dosage/frequency
                original_med = next((m for m in extracted_medicines if m.get('medicine') == validated_med.get('medicine')), {})
                
                final_medicines.append({
                    "medicine": medicine_name,
                    "dosage": original_med.get('dosage', ''),
                    "frequency": original_med.get('frequency', ''),
                    "extracted_by": "llama_extraction",
                    "validated_by": "llama_validation",
                    "validation_confidence": validated_med.get('confidence', 0),
                    "validation_notes": validated_med.get('validation_notes', '')
                })
        
        # Save final LLM validated medicines
        with open("outputs/step3_llm_validated_medicines.json", 'w', encoding='utf-8') as f:
            json.dump(final_medicines, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Final validated medicines: {[m['medicine'] for m in final_medicines]}")
        return final_medicines
        
    except Exception as e:
        logging.error(f"Medicine extraction/validation failed: {e}")
        return []
