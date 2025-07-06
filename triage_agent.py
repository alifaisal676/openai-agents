# triage_agent_openai_style.py

import json
from PIL import Image
import pytesseract
import ollama

# --- CONFIG ---
OLLAMA_MODEL = "phi3"  # Make sure it's pulled with: ollama pull phi3

class OpenAIStyleClient:
    """OpenAI SDK style wrapper for Ollama"""
    def __init__(self, model=OLLAMA_MODEL):
        self.model = model
        self.chat = self.Chat()
    
    class Chat:
        def __init__(self):
            self.completions = self.Completions()
        
        class Completions:
            def create(self, model, messages, **kwargs):
                response = ollama.chat(
                    model=model,
                    messages=messages
                )
                # Return OpenAI-style response structure
                return type('Response', (), {
                    'choices': [type('Choice', (), {
                        'message': type('Message', (), {
                            'content': response['message']['content']
                        })()
                    })()]
                })()

# Initialize client in OpenAI style
client = OpenAIStyleClient()

# --- OCR TOOL ---
def ocr_tool(image_path: str) -> str:
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text.strip()

# --- HELPER ---
def call_llm(prompt: str, system_message: str = "Respond only with valid JSON or one of the specified labels. No explanation.") -> str:
    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def clean_json_block(text):
    """Clean and fix common JSON formatting issues"""
    # Remove markdown code blocks
    if text.startswith('```'):
        lines = text.split('\n')
        lines = [line for line in lines if not line.strip().startswith('```')]
        text = '\n'.join(lines)
    
    # Remove any text before the first {
    start_idx = text.find('{')
    if start_idx != -1:
        text = text[start_idx:]
    
    # Remove any text after the last }
    end_idx = text.rfind('}')
    if end_idx != -1:
        text = text[:end_idx + 1]
    
    # Fix common JSON issues
    text = text.replace('\\n', ' ')  # Replace literal \n with spaces
    text = text.replace('\n', ' ')   # Replace actual newlines with spaces
    text = text.strip()
    
    return text

# --- AGENT CLASS ---
class Agent:
    def __init__(self, name, kind, ocr=None, handoffs=None):
        self.name = name
        self.kind = kind  # "triage", "lab", or "prescription"
        self.ocr = ocr
        self.handoffs = handoffs or []

    def run(self, input_data, is_image=False):
        print(f"\n=== Running Agent: {self.name} ===")

        # OCR if needed
        if is_image and self.ocr:
            print("[INFO] Running OCR...")
            text = self.ocr(input_data)
        else:
            text = input_data

        if self.kind == "triage":
            return self._triage(text)
        else:
            return self._extract_structured_data(text)

    def _triage(self, text: str):
        prompt = f"""
Classify the following document as either:
LabReport
DoctorPrescription

Respond with ONE of these two words only. No explanation.

Examples:
"Blood glucose: 89 mg/dL" => LabReport
"Amoxicillin 500mg, 2x daily" => DoctorPrescription

Text:
{text}
"""
        classification = call_llm(prompt, system_message="You are a classifier. Respond only with 'LabReport' or 'DoctorPrescription'. No extra words.")
        classification = classification.strip().lower()

        print(f"[INFO] Classified as: {classification}")

        if "labreport" in classification:
            return self.handoffs[0].run(text)
        elif "doctorprescription" in classification:
            return self.handoffs[1].run(text)
        else:
            return {
                "agent": self.name,
                "success": False,
                "error": "Unable to classify document.",
                "raw_output": classification
            }

    def _extract_structured_data(self, text: str):
        if self.kind == "lab":
            prompt = f"""
You extract structured data from a LAB REPORT.
Respond with VALID JSON only. No markdown. No explanation.

Format:
{{
  "tests": [
    {{ "test_name": "...", "result": "...", "unit": "...", "reference_range": "..." }}
  ],
  "patient_info": {{ "name": "...", "date": "..." }}
}}

Example:
{{
  "tests": [
    {{ "test_name": "Fasting Blood Sugar", "result": "89", "unit": "mg/dL", "reference_range": "70-100" }},
    {{ "test_name": "Insulin", "result": "22", "unit": "uU/mL", "reference_range": "2-25" }}
  ],
  "patient_info": {{ "name": "John Doe", "date": "2020-06-29" }}
}}

Report:
{text}
"""
        else:
            prompt = f"""
You extract structured data from a DOCTOR PRESCRIPTION.
Respond with VALID JSON only. No markdown. No explanation.

Format:
{{
  "doctor_info": {{ "name": "...", "license": "..." }},
  "patient_info": {{ "name": "...", "age": "..." }},
  "medications": [
    {{ "name": "...", "dosage": "...", "frequency": "..." }}
  ],
  "date": "..."
}}

Example:
{{
  "doctor_info": {{ "name": "Dr. Smith", "license": "12345" }},
  "patient_info": {{ "name": "Jane Doe", "age": "45" }},
  "medications": [
    {{ "name": "Amoxicillin", "dosage": "500mg", "frequency": "2x daily" }}
  ],
  "date": "2024-07-05"
}}

Prescription:
{text}
"""

        raw = call_llm(prompt, system_message="You are an extractor. Respond ONLY with valid JSON. No code blocks or commentary.")
        clean = clean_json_block(raw)

        try:
            parsed_data = json.loads(clean)
            return {
                "agent": self.name,
                "success": True,
                "data": parsed_data
            }
        except json.JSONDecodeError as e:
            # Try to fix common issues and retry
            try:
                # Remove extra escape characters and fix quotes
                fixed = clean.replace('\\"', '"').replace('\\\\', '\\')
                parsed_data = json.loads(fixed)
                return {
                    "agent": self.name,
                    "success": True,
                    "data": parsed_data
                }
            except json.JSONDecodeError:
                return {
                    "agent": self.name,
                    "success": False,
                    "raw_response": raw,
                    "cleaned_response": clean,
                    "error": f"Failed to parse JSON: {str(e)}"
                }

# --- MAIN ---
if __name__ == "__main__":
    # Create individual agents
    lab_agent = Agent(name="lab_report_agent", kind="lab")
    prescription_agent = Agent(name="doctor_prescription_agent", kind="prescription")

    # Create triage agent with OCR and routing
    triage_agent = Agent(
        name="triage_agent",
        kind="triage",
        handoffs=[lab_agent, prescription_agent],
        ocr=ocr_tool
    )

    # INPUT (Image path or raw text)
    IMAGE_PATH = "lab_report.png"  # Change to your file

    # Run the agent
    result = triage_agent.run(IMAGE_PATH, is_image=True)

    print("\n=== FINAL RESULT ===")
    try:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (TypeError, ValueError) as e:
        print(f"Error formatting result as JSON: {e}")
        print("Raw result:")
        print(result)
