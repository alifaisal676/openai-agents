
# Lab Report Batch Processor

This project provides a **unified OpenAI SDK multi-agent system** for processing lab report images (single or batch) using intelligent agent orchestration with function calling.

## Features
- **🤖 OpenAI SDK Multi-Agent Architecture:** LLM agent decides which tools to call and when
- **⚡ Batch Processing:** Process multiple lab reports in one go
- **🔧 Three Agent Tools:**
  1. **OCR Extraction** (Tesseract): Extracts text from lab report images
  2. **LLM Structuring:** Converts raw text into structured JSON
  3. **Pydantic Validation:** Validates and cleans the structured data
- **📊 Smart Output Organization:**
  - Individual JSON files per image: `{image_name}_structured.json`
  - OCR text files: `{image_name}_ocr.txt` 
  - Batch summary: `processing_summary.json`
- **🚀 Optimized Performance:** 10.5s average per image with agent intelligence

## Requirements
- Python 3.8+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and in your PATH
- Python packages:
  - `openai` (Groq SDK compatible)
  - `python-dotenv`
  - `pillow`
  - `pytesseract`

Install dependencies:
```sh
pip install openai python-dotenv pillow pytesseract
```

## Setup
1. **Set your Groq/OpenAI API key:**
   - Create a `.env` file in the project directory:
     ```
     GROQ_API_KEY=your_groq_api_key_here
     ```
2. **Ensure Tesseract is installed and available in your PATH.**

## Usage

### **Batch Processing (Recommended)**
Process multiple lab report images at once:
```bash
python batch_processor.py
```
- Processes all images in `lab_images/` directory
- Outputs organized results in `processed_reports/` directory  
- Generates comprehensive batch summary

### **Custom Directories**
Modify the script or update these variables:
```python
INPUT_DIR = "lab_images"      # Your input directory
OUTPUT_DIR = "processed_reports"  # Your output directory
```

## How it Works
1. **🔍 Discovery:** Finds all image files (.png, .jpg, .jpeg, .tiff, .bmp)
2. **🤖 Agent Processing:** For each image:
   - Agent conversation loop with OpenAI SDK
   - OCR → LLM Structuring → Pydantic Validation
   - Intelligent tool calling decisions
3. **💾 Smart Storage:** Organized file output with batch statistics

## Output Structure
```
processed_reports/
├── processing_summary.json          # Batch statistics
├── {image1}_structured.json         # Structured lab data
├── {image2}_structured.json         
├── ocr_outputs/                     # Organized OCR text files
│   ├── {image1}_ocr.txt             # Raw OCR text  
│   ├── {image2}_ocr.txt
│   └── ...
└── ...
```

## Customization
- **Tools:** Modify OCR, LLM, or validation functions in `batch_processor.py`
- **Agent Behavior:** Update system prompts and tool definitions
- **Output Format:** Adjust Pydantic models for different lab report formats

---
**Author:** Ali Faisal
