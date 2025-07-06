# Triage Agent (Ollama + OpenAI SDK Style)

This project is an intelligent triage agent for medical documents (lab reports and doctor prescriptions). It uses OCR to extract text from images, classifies the document type, and extracts structured data using a local Ollama LLM, all with an interface similar to the OpenAI SDK.

## Features
- **OCR**: Extracts text from medical images (lab reports, prescriptions)
- **Classification**: Determines if the document is a lab report or a prescription
- **Structured Extraction**: Extracts relevant fields as JSON
- **OpenAI SDK Style**: Code is structured to easily swap between Ollama and OpenAI APIs
- **No Paid API Required**: Runs fully locally with Ollama

## Requirements
- Python 3.8+
- [Ollama](https://ollama.com/) (with the `phi3` model pulled)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- Python packages: `pillow`, `pytesseract`, `ollama`

## Setup
1. **Clone this repository**
2. **Install Python dependencies:**
   ```bash
   pip install pillow pytesseract ollama
   ```
3. **Install Tesseract OCR:**
   - Windows: Download from [here](https://github.com/tesseract-ocr/tesseract/wiki)
   - Linux: `sudo apt-get install tesseract-ocr`
   - Mac: `brew install tesseract`
4. **Install Ollama and pull the model:**
   ```bash
   ollama pull phi3
   ollama serve
   ```
5. **Add your image files** (e.g., `lab_report.png`, `prescription_sample.png`) to the project directory.

## Usage
Run the triage agent on an image:
```bash
python triage_agent.py
```
- The script will OCR the image, classify it, and extract structured data as JSON.
- Change the `IMAGE_PATH` variable in `triage_agent.py` to test different files.

## Example Output
```
=== FINAL RESULT ===
{
  "agent": "lab_report_agent",
  "success": true,
  "data": {
    "tests": [
      { "test_name": "Fasting Blood Sugar", "result": "89", "unit": "mg/dL", "reference_range": "70-100" },
      { "test_name": "Insulin", "result": "22", "unit": "uU/mL", "reference_range": "2-25" }
    ],
    "patient_info": { "name": "John Doe", "date": "2020-06-29" }
  }
}
```

## Project Structure
- `triage_agent.py` — Main agent code
- `lab_report.png`, `prescription_sample.png` — Example images

## License
This project is for educational and research purposes.
