"""
🧠 Medicine Validation Module
Handles AI-powered validation of extracted medicine names.
"""

import json
import re
from openai import OpenAI
import logging

def smart_medicine_validation(potential_medicines, groq_api_key, groq_endpoint):
    """🧠 AI validation with medicine database context"""
    try:
        logging.info("Using AI to validate medicine names with database context...")
        
        # Load medicine database for validation context
        try:
            from .database_utils import load_trusted_medicine_database
            medicine_database = load_trusted_medicine_database("medicines_pk.js")
            sample_medicines = medicine_database[:150]  # More samples for validation
            database_context = ", ".join(sample_medicines)
        except:
            database_context = "Amoxicillin, Aspirin, Metformin, Paracetamol, Ibuprofen"  # Fallback
        
        ai_client = OpenAI(api_key=groq_api_key, base_url=groq_endpoint)
        medicines_for_review = json.dumps(potential_medicines, indent=2)
        
        validation_instructions = f"""You are a medical expert with access to a medicine database. For each name below, determine if it's a real pharmaceutical drug.

Names to check:
{medicines_for_review}

MEDICINE DATABASE CONTEXT:
Here are examples from our verified medicine database: {database_context}...

VALIDATION STRATEGY:
1. Check if the name appears in or closely resembles medicines from the database context above
2. Consider that names found WITH dosages are more likely to be medicines
3. Look for partial matches - "Myl" might be part of "Mylène" which could be a medicine
4. Consider international medicine names and brand names

IMPORTANT CONSIDERATIONS:
- Names with dosages (4mg, 500mg, etc.) are strong indicators of medicines
- Some medicine names may resemble person names but are actually drugs
- Check for fuzzy matches with the database context provided
- Be more lenient if the name could plausibly be a medicine

Examples:
- "Keviy" alone = Person name (NOT medicine)
- "Mylène" with dosage = Could be medicine name (check database context)
- "Tras" with dosage = Could be truncated medicine name (IS medicine)
- Names similar to database entries = Likely medicines

Respond with JSON:
[
  {{
    "medicine": "original_name",
    "is_valid_medicine": true/false,
    "validation_notes": "brief reason including database check",
    "confidence": 0.9
  }}
]"""

        ai_validation_response = ai_client.chat.completions.create(
            model="llama3-70b-8192",  # Using the larger model for better medical knowledge
            messages=[
                {"role": "system", "content": "You are a medical validation expert with access to a medicine database. Use both your knowledge and the provided database context to validate medicine names. Respond only with valid JSON."},
                {"role": "user", "content": validation_instructions}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        validation_result = ai_validation_response.choices[0].message.content
        logging.info(f"AI Validation completed. Preview: {validation_result[:200]}...")
        
        # Save validation details for debugging
        with open("outputs/llama_validation_response.txt", 'w', encoding='utf-8') as f:
            f.write(f"VALIDATION PROMPT:\n{validation_instructions}\n\n")
            f.write(f"LLAMA VALIDATION RESPONSE:\n{validation_result}")
        
        # Parse AI validation response with error handling
        try:
            json_match = re.search(r'\[.*?\]', validation_result, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
            else:
                json_text = validation_result.strip()
            
            try:
                validated_medicines = json.loads(json_text)
            except json.JSONDecodeError as e:
                print(f"   ⚠️ Validation JSON parsing failed: {e}")
                
                # Clean up common JSON issues
                cleaned_json = json_text.replace("'", '"')
                cleaned_json = re.sub(r',\s*}', '}', cleaned_json)
                cleaned_json = re.sub(r',\s*]', ']', cleaned_json)
                
                try:
                    validated_medicines = json.loads(cleaned_json)
                    print("   ✅ Validation JSON parsing succeeded after cleanup")
                except json.JSONDecodeError as e2:
                    print(f"   ❌ Validation JSON parsing failed even after cleanup: {e2}")
                    print(f"   📝 Problematic JSON: {json_text[:200]}...")
                    return []
            
            return validated_medicines if isinstance(validated_medicines, list) else []
            
        except Exception as parsing_error:
            logging.error(f"JSON parsing failed: {parsing_error}")
            return []
            
    except Exception as validation_error:
        logging.error(f"Medicine validation failed: {validation_error}")
        return []

def fallback_medicine_validation(medicines, groq_key, groq_endpoint):
    """🔄 Fallback validation with specific pharmaceutical queries"""
    try:
        logging.info("Using fallback validation with specific drug queries...")
        
        client = OpenAI(api_key=groq_key, base_url=groq_endpoint)
        validated_results = []
        
        for medicine in medicines:
            medicine_name = medicine.get('medicine', '')
            
            specific_prompt = f"""As a pharmaceutical expert, determine if "{medicine_name}" is a legitimate medication.

Consider: Generic names, brand names, international variants, antibiotics, etc.

Respond with JSON:
{{
  "medicine": "{medicine_name}",
  "is_valid_medicine": true/false,
  "validation_notes": "explanation",
  "confidence": 0.85
}}

Be generous - if there's reasonable chance this is a medicine, mark valid."""

            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are a pharmaceutical database expert. Be inclusive in your validation."},
                    {"role": "user", "content": specific_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            try:
                result_text = response.choices[0].message.content
                json_match = re.search(r'\{.*?\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                    validated_results.append(result)
                    print(f"  Fallback check: {medicine_name} → {result.get('is_valid_medicine', False)}")
            except Exception as e:
                print(f"  Fallback parsing failed for {medicine_name}: {e}")
                continue
        
        return validated_results
        
    except Exception as e:
        print(f"Fallback validation failed: {e}")
        return []
