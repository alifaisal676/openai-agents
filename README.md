# 🏥 Smart Prescription Processing System

An intelligent prescription reader that extracts medicine information from prescription images using Azure OCR and LLaMA AI with advanced validation.

## ✨ Features

- **🖼️ Smart Image Enhancement**: Automatically improves prescription image quality for better text recognition
- **📄 Azure OCR Integration**: Powerful text extraction from prescription images
- **🤖 LLaMA AI Processing**: Intelligent medicine extraction using state-of-the-art AI
- **🧠 Dual AI Validation**: Smart filtering to avoid false positives like person names
- **📚 Database Cross-Reference**: Validates medicines against trusted medicine database
- **🎯 Modular Architecture**: Clean, organized code structure with separate modules
- **📊 Professional Logging**: Timestamped logging for production use

## 🚀 Quick Start

1. **Install Dependencies**
```bash
pip install opencv-python requests rapidfuzz python-dotenv openai
```

2. **Setup Environment**
Create `.env` file:
```env
AZURE_OCR_ENDPOINT=your_azure_endpoint
AZURE_OCR_KEY=your_azure_key
GROQ_API_KEY=your_groq_api_key
```

3. **Run the Pipeline**
```bash
python run_prescription_processor.py
```

## 📋 How It Works

1. **📸 Image Enhancement**: Converts to grayscale, removes noise, enhances contrast
2. **🔍 Text Extraction**: Uses Azure OCR to read all text from the prescription
3. **🧹 Text Cleaning**: Standardizes spacing, removes special characters
4. **🤖 AI Extraction**: LLaMA AI intelligently finds medicine names, dosages, frequencies
5. **✅ Smart Validation**: Filters out person names, clinic names, and false positives
6. **📚 Database Verification**: Cross-checks against known medicine database with fuzzy matching

## 🏗️ Modular Architecture

The system is organized into clean, focused modules:

- **`prescription_processor/`** - Main package
  - `pipeline.py` - Main orchestration workflow
  - `image_processor.py` - CV2 image enhancement
  - `ocr_processor.py` - Azure OCR text extraction
  - `llama_extractor.py` - AI medicine extraction
  - `medicine_validator.py` - AI validation
  - `database_utils.py` - Medicine database operations
- **`run_prescription_processor.py`** - Main entry point
- **`medicines_pk.js`** - Medicine database

## 📁 Input & Output

**Input**: Place your prescription image as `pic3.jpeg` in the project folder

**Output**: Clean JSON with extracted medicines:
```json
[
  {
    "medicine": "Mylène",
    "dosage": "4mg",
    "frequency": "unknown",
    "confidence": 85.2
  }
]
```

## 💻 Usage Examples

**Basic Usage:**
```python
from prescription_processor import process_prescription

# Process a prescription image
result = process_prescription("pic3.jpeg")
print(result)
```

**Command Line:**
```bash
python run_prescription_processor.py
```

## 📂 Output Files

The pipeline saves detailed outputs in the `outputs/` folder:
- `ocr_raw.txt` - Raw text from Azure OCR
- `ocr_cleaned.txt` - Cleaned and standardized text
- `step1_extracted_medicines.json` - Initial AI extraction
- `step2_validation_response.json` - AI validation results
- `step3_llm_validated_medicines.json` - Filtered valid medicines
- `step4_final_with_database.json` - Final results with database matching

## 🔧 Requirements

- Python 3.7+
- Azure Computer Vision API (for OCR)
- Groq API (for LLaMA AI)
- `medicines_pk.js` database file (included)

## 🎯 Key Improvements

- **Modular Architecture**: Clean separation of concerns with focused modules
- **Professional Logging**: Timestamped logging instead of print statements
- **Smart Validation**: Distinguishes between real medicines and person names
- **Database Context**: Uses medicine database to guide AI extraction
- **Simple & Clean**: Humanized code without over-engineering
- **Production Ready**: Proper package structure and error handling

## 🚫 Anti-Hallucination Features

- Dual LLaMA validation (extraction + verification)
- Database-contextual AI prompting
- Confidence thresholds to filter weak matches
- Medicine database cross-referencing with fuzzy matching
- Conservative validation approach

## 📜 License

MIT License

---

**Author**: AI Assistant (Humanized Version)  
**Purpose**: Medical prescription digitization with intelligent validation
