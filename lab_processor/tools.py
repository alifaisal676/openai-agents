import json
import re
import time
from pathlib import Path
from PIL import Image
import pytesseract
from openai import OpenAI

from .config import GROQ_API_KEY, GROQ_BASE_URL, MODEL_NAME, MAX_TOKENS, TIMEOUT, TEMPERATURE, STRUCTURE_PROMPT
from .models import validate_lab_data

from langsmith import traceable


# Initialize OpenAI client
client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)

@traceable(name="extract_text")
def extract_text_from_image(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        raise Exception(f"OCR failed: {str(e)}")
    
    
@traceable(name="structure_data")
def structure_text_data(text: str) -> dict:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": STRUCTURE_PROMPT},
                {"role": "user", "content": f"Extract JSON from:\n{text}"}
            ],
            max_tokens=MAX_TOKENS,
            timeout=TIMEOUT,
            temperature=TEMPERATURE
        )
        
        content = response.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if match:
            return json.loads(match.group(0))
        else:
            return {"error": "No JSON found in response"}
            
    except Exception as e:
        return {"error": f"Structuring failed: {str(e)}"}


@traceable(name="validate_data")
def validate_structured_data(data: dict) -> dict:
    return validate_lab_data(data)



def save_ocr_output(text: str, output_dir: Path, filename: str):
    ocr_dir = output_dir / "ocr_outputs"
    ocr_dir.mkdir(exist_ok=True)
    
    ocr_file = ocr_dir / f"{filename}_ocr.txt"
    with open(ocr_file, "w", encoding="utf-8") as f:
        f.write(text)
    
    return ocr_file



def save_structured_data(data: dict, output_file: Path):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
