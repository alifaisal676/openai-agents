

import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def ocr_lab_report_image(image_path: str) -> str:
    """Extract text from a lab report image using Tesseract OCR."""
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        raise ImportError("Please install Pillow and pytesseract: pip install pillow pytesseract")
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)





def llm_structure_lab_report_text(lab_report_text: str) -> dict:
    """Use LLM to convert lab report text into structured JSON data."""
    system_prompt = (
        "You are a medical data assistant. Given the raw text of a lab report, extract the following fields as JSON: "
        "patient_name, age, gender, doctor_name, date, comments, and test_results (list of dicts with test_name, value, unit, reference_range). "
        "If a field is missing, use an empty string."
    )
    user_prompt = f"Lab Report Text:\n{lab_report_text}\n\nReturn only the JSON object."
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1024
    )
    import re
    match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return {"error": "Could not extract JSON from LLM response.", "raw": response.choices[0].message.content}






def postprocess_lab_report_data(structured_data: dict) -> dict:
    """Refine structured lab data: strip whitespace, normalize, convert types, remove empty results."""
    import copy
    data = copy.deepcopy(structured_data)
    for key in ["patient_name", "age", "gender", "doctor_name", "date", "comments"]:
        if key in data and isinstance(data[key], str):
            data[key] = data[key].strip()
        elif key not in data:
            data[key] = ""
    refined_results = []
    for test in data.get("test_results", []):
        if not any(test.values()):
            continue
        refined = {}
        refined["test_name"] = test.get("test_name", "").strip().capitalize()
        val = test.get("value", "").strip()
        try:
            refined["value"] = float(val) if val else ""
        except Exception:
            refined["value"] = val
        refined["unit"] = test.get("unit", "").strip()
        refined["reference_range"] = test.get("reference_range", "").strip()
        refined_results.append(refined)
    data["test_results"] = refined_results
    return data






tools = [
    {
        "type": "function",
        "function": {
            "name": "ocr_lab_report_image",
            "description": "Extract text from a lab report image using Tesseract OCR.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "Path to the lab report image file."}
                },
                "required": ["image_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "llm_structure_lab_report_text",
            "description": "Convert lab report text into structured JSON using an LLM.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab_report_text": {"type": "string", "description": "Raw text from the lab report."}
                },
                "required": ["lab_report_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "postprocess_lab_report_data",
            "description": "Refine structured lab report data using Python logic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "structured_data": {"type": "object", "description": "Structured lab report data as a dict."}
                },
                "required": ["structured_data"]
            }
        }
    }
]






def agent_lab_report(image_path=None, text_input=None, output_file="structured_output.txt"):
    """Agent pipeline: LLM decides which tool(s) to call and in what order. Handles image or text input."""
    messages = [
        {"role": "system", "content": (
            "You are a medical lab report assistant. You have access to three tools: "
            "1. OCR extraction from image, 2. LLM-based structuring, 3. Python post-processing. "
            "Given an image or text, use the tools as needed to extract, structure, and refine lab report data. "
            "Save the OCR text to ocr_output.txt and the final structured data to lab_report_output.txt. "
            "Call tools as needed and return only the final structured data as your answer."
        )}
    ]
    if image_path:
        user_content = f"Please process this lab report image: {image_path}"
    elif text_input:
        user_content = f"Please process this lab report text:\n{text_input}"
    else:
        raise ValueError("Either image_path or text_input must be provided.")
    messages.append({"role": "user", "content": user_content})

    tool_functions = {
        "ocr_lab_report_image": ocr_lab_report_image,
        "llm_structure_lab_report_text": llm_structure_lab_report_text,
        "postprocess_lab_report_data": postprocess_lab_report_data
    }

    ocr_text = None
    structured = None
    refined = None
    
    
    
    

    while True:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=1024
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                result = tool_functions[tool_name](**tool_args)
                if tool_name == "ocr_lab_report_image":
                    ocr_text = result
                    with open("ocr_output.txt", "w", encoding="utf-8") as f:
                        f.write(ocr_text)
                    print("[INFO] OCR extraction complete.")
                if tool_name == "llm_structure_lab_report_text":
                    structured = result
                    print("[INFO] Lab report structured.")
                if tool_name == "postprocess_lab_report_data":
                    refined = result
                    print("[INFO] Data post-processed.")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(result) if not isinstance(result, str) else result
                })
        else:
            final_content = msg.content
            if refined:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(json.dumps(refined, indent=2))
                print(f"[SUCCESS] Final structured lab report data saved to: {output_file}")
            elif structured:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(json.dumps(structured, indent=2))
                print(f"[SUCCESS] Final structured lab report data saved to: {output_file}")
            else:
                print("[INFO] No structured data to save.")
            return final_content





if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python structure2.py <path_to_lab_report_image>")
        sys.exit(1)
    image_path = sys.argv[1]
    agent_lab_report(image_path=image_path)
