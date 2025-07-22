
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

## Database Integration 🗄️

### **Option 1: Supabase (Recommended - Cloud)**

Easy cloud PostgreSQL setup with Supabase:

```bash
# Install dependencies
pip install psycopg2-binary supabase

# Configure Supabase in .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_DB_PASSWORD=your_db_password

# Transfer to Supabase
python supabase_transfer.py
```

**Supabase Setup Steps:**
1. 🌐 Go to [supabase.com](https://supabase.com) and create account
2. 🆕 Create new project
3. 🔑 Copy URL, anon key, and database password to `.env`
4. 🚀 Run `python supabase_transfer.py`

### **Option 2: Local PostgreSQL**

Transfer processed lab reports to local PostgreSQL database:

```bash
# Install database dependencies
pip install psycopg2-binary

# Configure database in .env file
DB_HOST=localhost
DB_NAME=lab_reports
DB_USER=postgres
DB_PASSWORD=your_password

# Transfer structured data to database
python database_transfer.py
```

**Database Features:**
- 📊 **Automatic Schema Creation:** `patients` and `lab_tests` tables
- 🔄 **Duplicate Prevention:** Smart conflict resolution 
- 📈 **Normalized Structure:** Proper relationships and indexes
- 🛡️ **Error Handling:** Transaction safety and rollbacks

See `DATABASE_SETUP_GUIDE.md` for detailed setup instructions.

## Complete Workflow 🔄

### **With Supabase (Recommended)**
```bash
1. python batch_processor.py     # Process images → JSON
2. python supabase_transfer.py   # JSON → Supabase Cloud DB
```

### **With Local PostgreSQL**
```bash
1. python batch_processor.py    # Process images → JSON
2. python database_transfer.py  # JSON → Local PostgreSQL
```

## Customization
- **Tools:** Modify OCR, LLM, or validation functions in `batch_processor.py`
- **Agent Behavior:** Update system prompts and tool definitions
- **Output Format:** Adjust Pydantic models for different lab report formats
- **Database Schema:** Extend tables in `database_transfer.py`

---
**Author:** Ali Faisal
