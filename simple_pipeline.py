import os
import json
import time
import re
import requests
import cv2
from rapidfuzz import fuzz, process
from dotenv import load_dotenv
from openai import OpenAI
from transformers import BioGptTokenizer, BioGptForCausalLM
import torch

def enhance_image(img_path):
    try:
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        enhanced_path = "temp_enhanced.png"
        cv2.imwrite(enhanced_path, enhanced)
        return enhanced_path
    except:
        return img_path

def azure_ocr(img_path, endpoint, key):
    with open(img_path, 'rb') as f:
        image_data = f.read()
    
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Content-Type': 'application/octet-stream'
    }
    
    url = f"{endpoint.rstrip('/')}/vision/v3.2/read/analyze"
    response = requests.post(url, headers=headers, data=image_data)
    
    if response.status_code != 202:
        print(f"OCR Error: {response.text}")
        response.raise_for_status()
    
    operation_url = response.headers['Operation-Location']
    
    # Wait for processing
    while True:
        result = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': key})
        data = result.json()
        
        if data['status'] == 'succeeded':
            break
        elif data['status'] == 'failed':
            raise Exception("OCR failed")
        time.sleep(2)
    
    # Extract text
    text = ""
    for page in data['analyzeResult']['readResults']:
        for line in page['lines']:
            text += line['text'] + '\n'
    
    return text

def clean_text(raw_text):
    # Basic text cleaning
    text = re.sub(r'\n+', ' ', raw_text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\+\-\.\,\:\;\(\)\[\]\/]', ' ', text)
    text = re.sub(r'\s*\+\s*', '+', text)
    text = re.sub(r'\s*mg\s*', 'mg ', text)
    return text.strip()

def query_biogpt(prompt):
    try:
        print("Loading BioGPT...")
        
        os.environ["TRANSFORMERS_VERBOSITY"] = "error"
        
        tokenizer = BioGptTokenizer.from_pretrained("microsoft/biogpt", local_files_only=True)
        model = BioGptForCausalLM.from_pretrained(
            "microsoft/biogpt", 
            local_files_only=True,
            use_safetensors=False
        )
        
        model.to("cpu")
        model.eval()
        
        full_prompt = f"Prescription: {prompt}\nMedicine names:"
        
        inputs = tokenizer(
            full_prompt, 
            return_tensors="pt", 
            max_length=200,
            truncation=True,
            padding=True
        )
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                num_return_sequences=1,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                repetition_penalty=1.5
            )
        
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = generated[len(full_prompt):].strip()
        
        print("Got BioGPT response")
        return response
        
    except Exception as e:
        print(f"BioGPT failed: {e}")
        return ""

def query_llama_groq(prompt, groq_key, groq_endpoint):
    try:
        client = OpenAI(api_key=groq_key, base_url=groq_endpoint)
        
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a medical prescription analyzer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"LLaMA failed: {e}")
        return ""

def extract_medicines_with_llm(text, model, **kwargs):
    
    if model.lower() == "biogpt":
        print("Using BioGPT...")
        
        medicines = []
        words = text.split()
        
        # Skip common words that aren't medicines
        skip_words = ['name', 'age', 'date', 'patient', 'medicine', 
                     'text', 'drug', 'drugs', 'prescription', 'clear', 'found']
        
        for word in words:
            if (len(word) > 3 and 
                word[0].isupper() and 
                word.isalpha() and
                word.lower() not in skip_words):
                
                dosage = ""
                frequency = ""
                
                # Look around this word for dosage info
                try:
                    idx = words.index(word)
                    for i in range(max(0, idx-2), min(len(words), idx+3)):
                        nearby = words[i]
                        if any(unit in nearby.lower() for unit in ['mg', 'ml', 'g', 'tab']) and any(c.isdigit() for c in nearby):
                            dosage = nearby
                        if any(freq in nearby.lower() for freq in ['bd', 'td', 'od', 'qd', 'tds']):
                            frequency = nearby
                except:
                    pass
                
                medicines.append({
                    "medicine": word,
                    "dosage": dosage,
                    "frequency": frequency
                })
        
        print(f"Found {len(medicines)} medicines: {[m['medicine'] for m in medicines]}")
        return medicines
        
    elif model.lower() == "llama":
        print("Using LLaMA...")
        
        prompt = f'''Extract medicine info from this prescription:

Text: "{text}"

Return JSON like:
[
  {{
    "medicine": "name",
    "dosage": "amount",
    "frequency": "how often"
  }}
]

Return [] if no medicines found.'''
        
        groq_key = kwargs.get('groq_key')
        groq_endpoint = kwargs.get('groq_endpoint', 'https://api.groq.com/openai/v1')
        
        if not groq_key:
            print("Need Groq API key for LLaMA")
            return []
        
        response = query_llama_groq(prompt, groq_key, groq_endpoint)
        
        try:
            # Try to find JSON in response
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result if isinstance(result, list) else []
            else:
                result = json.loads(response)
                return result if isinstance(result, list) else []
        except Exception as e:
            print(f"JSON parsing failed: {e}")
            return []
        
    else:
        print(f"Unknown model: {model}")
        return []

def load_medicines_database(js_path):
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'var\s+\w+\s*=\s*\[(.*?)\];', content, re.DOTALL)
    if not match:
        return []
    
    return re.findall(r'"([^"]*)"', match.group(1))

def validate_medicines(medicines, known_meds):
    validated = []
    for med in medicines:
        name = med.get('medicine', '').strip()
        if not name:
            continue
            
        best_match, confidence, _ = process.extractOne(name, known_meds, scorer=fuzz.ratio)
        
        new_med = med.copy()
        if confidence >= 90:
            new_med['medicine'] = best_match
        new_med['confidence'] = confidence
        validated.append(new_med)
    
    return validated

def process_prescription(
    image_path,
    azure_endpoint,
    azure_key,
    model="llama",
    groq_api_key=None,
    medicines_js_path="medicines.js",
    output_dir="."
):
    
    try:
        print("Processing prescription...")
        print(f"Using {model.upper()}")
        
        # Create output folder
        os.makedirs(os.path.join(output_dir, "outputs"), exist_ok=True)
        
        # Enhance image
        enhanced_path = enhance_image(image_path)
        
        # Get text from image
        raw_text = azure_ocr(enhanced_path, azure_endpoint, azure_key)
        with open(os.path.join(output_dir, "outputs/ocr_raw.txt"), 'w', encoding='utf-8') as f:
            f.write(raw_text)
        
        # Clean text
        cleaned_text = clean_text(raw_text)
        with open(os.path.join(output_dir, "outputs/ocr_cleaned.txt"), 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        # Extract medicines
        extracted = extract_medicines_with_llm(
            text=cleaned_text,
            model=model,
            groq_key=groq_api_key
        )
        with open(os.path.join(output_dir, "outputs/output_raw.json"), 'w', encoding='utf-8') as f:
            json.dump(extracted, f, indent=2, ensure_ascii=False)
        
        # Validate medicines
        known_medicines = load_medicines_database(medicines_js_path)
        validated = validate_medicines(extracted, known_medicines)
        with open(os.path.join(output_dir, "outputs/output_validated.json"), 'w', encoding='utf-8') as f:
            json.dump(validated, f, indent=2, ensure_ascii=False)
        
        # Cleanup
        if enhanced_path != image_path and os.path.exists(enhanced_path):
            os.remove(enhanced_path)
        
        print("Done!")
        return {
            "success": True,
            "model_used": model,
            "medicines_extracted": len(extracted),
            "medicines_validated": len(validated),
            "files": ["ocr_raw.txt", "ocr_cleaned.txt", "output_raw.json", "output_validated.json"]
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": str(e), "model_used": model}

def main():
    load_dotenv()
    
    model = "biogpt"  # or "llama"
    
    azure_endpoint = os.getenv('AZURE_OCR_ENDPOINT')
    azure_key = os.getenv('AZURE_OCR_KEY')
    groq_api_key = os.getenv('GROQ_API_KEY')
    
    if model == "llama" and not all([azure_endpoint, azure_key, groq_api_key]):
        print("Missing environment variables for LLaMA")
        return
    elif model == "biogpt" and not all([azure_endpoint, azure_key]):
        print("Missing environment variables for BioGPT")
        return
    
    result = process_prescription(
        image_path="pic.jpg",
        azure_endpoint=azure_endpoint,
        azure_key=azure_key,
        model=model,
        groq_api_key=groq_api_key
    )
    
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
