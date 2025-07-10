
# Lab Report Agent Pipeline

This project provides an **agent-based Python pipeline** for extracting structured data from lab report images using the OpenAI (Groq) SDK with function calling (tools).

## Features
- **Agent Orchestration:** The LLM decides which tool(s) to call and in what order.
- **Tools Provided:**
  1. **OCR Extraction** (Tesseract): Extracts text from lab report images.
  2. **LLM Structuring:** Converts lab report text into structured JSON.
  3. **Post-processing:** Cleans and normalizes the structured data.
- **Outputs:**
  - Raw OCR text → `ocr_output.txt`
  - Final structured data → `structured_output.txt`
- **Minimal logs** and modular, well-documented code.

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
Run the script from the command line:
```sh
python structure2.py <path_to_lab_report_image>
```
- The agent will process the image, using the tools as needed.
- Results are saved to `ocr_output.txt` and `structured_output.txt`.

## How it Works
- The LLM agent receives your request and can call any of the three tools (OCR, structuring, post-processing) in any order, as needed.
- The agent loop continues until the LLM returns a final answer.
- All tool calls and results are handled automatically.

## Customization
- You can extend or modify the tools in `structure2.py`.
- The agent prompt and tool metadata can be adjusted for different workflows.

---
**Author:** Ali Faisal
