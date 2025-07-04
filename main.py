import sys
import json
from api import groq_client
from ocr import ocr_image
from classifier import classify_document
from parsers import parse_lab_report, parse_prescription

def triage_pipeline(input_path_or_text: str, is_image: bool):
    # 1. OCR or use text
    if is_image:
        text = ocr_image(input_path_or_text)
    else:
        text = input_path_or_text

    # 2. Classification
    label = classify_document(
        text,
        groq_client
    )
    print(f"Classification: {label}")




    if label == "LabReport":
        json_output = parse_lab_report(text, groq_client)
    elif label == "DoctorPrescription":
        json_output = parse_prescription(text, groq_client)
    else:
        raise ValueError(f"Unexpected classification: {label}")

        

    try:
        parsed_json = json.loads(json_output)
        print(json.dumps(parsed_json, indent=2))
    except json.JSONDecodeError:
    # If the parser already returned a pretty JSON string, just print as is
        print(json_output.strip())

# Example usage
if __name__ == "__main__":
    # python main.py path/to/image.jpg
    if len(sys.argv) < 2:
        print("Usage: python main.py <file_path>")
        sys.exit(1)


    triage_pipeline(sys.argv[1], is_image=True)  # For image input
    # triage_pipeline("Sample text input for testing", is_image=False)  # For text input    