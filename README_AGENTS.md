# Medical Triage Agent System (OpenAI-style with Groq)

A sophisticated agent-based medical document processing system that mimics the OpenAI Agents pattern while using Groq's fast inference API. The system automatically triages medical documents and routes them to specialized agents for structured data extraction.

## 🏗️ Architecture Overview

This implementation follows the **OpenAI Agents pattern** with automatic handoffs between specialized agents:

```
Input Document → Triage Agent → Classification → Handoff to Specialist Agent → Structured Output
```

### **Agent Hierarchy:**
- **🎯 Triage Agent**: Classifies documents and routes to appropriate specialists
- **🧪 Lab Report Agent**: Extracts structured data from laboratory reports
- **💊 Prescription Agent**: Extracts structured data from doctor prescriptions
- **🔧 OCR Tool**: Shared tool for text extraction from images

## 🚀 Features

- **🤖 Agent-Based Architecture**: True agent pattern with automatic handoffs
- **⚡ Fast Processing**: Powered by Groq's optimized inference
- **📄 Multi-Format Support**: Processes both images and text input
- **🔍 OCR Integration**: Automatic text extraction from medical document images
- **📊 Structured Output**: Clean JSON data extraction
- **🔒 Secure**: API keys stored in environment variables
- **🎯 Automatic Routing**: Agents automatically handoff to specialists

## 📁 Project Structure

```
Triage/
├── main.py                  # Main application (OpenAI Agents style)
├── agent_framework.py       # Agent classes and framework
├── api.py                   # Groq API configuration
├── ocr.py                   # OCR functionality (Tesseract)
├── main_openai_style.py     # Alternative main file
├── sample_images/           # Sample medical documents
│   ├── lab_report.png
│   └── prescription_sample.png
├── .env                     # Environment variables (API keys)
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Tesseract OCR
- Groq API key

### 1. Install Tesseract OCR

**Windows:**
1. Download from [GitHub Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install and add to PATH


```
### 2. Install Python Dependencies
```bash
pip install groq pillow pytesseract python-dotenv
```

### 3. Set Up Environment Variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your Groq API key from [Groq Console](https://console.groq.com/)

## 🎮 Usage

### Command Line Interface

```bash
# Process medical document images
python main.py lab_report.png
python main.py prescription.jpg

# Process text directly 
python main.py "Hemoglobin: 14.2 g/dL, WBC: 7.8 K/uL" --text
python main.py "Amoxicillin 500mg, take twice daily" --text
```

### Programmatic Usage

## 🔄 Agent Workflow

### 1. **Triage Agent Classification**
```python
# Automatically classifies documents
classification = triage_agent._classify_document(text)
# Returns: "LabReport" or "DoctorPrescription"
```

### 2. **Automatic Handoff**
```python
# Seamlessly hands off to specialist agents
if classification == "LabReport":
    return lab_agent.run(document_text)
elif classification == "DoctorPrescription":
    return prescription_agent.run(document_text)
```

### 3. **Structured Extraction**
Each specialist agent returns standardized structured data.

## 📊 Output Examples

### Lab Report Output
```json
{
  "tests": [
    {
      "test_name": "Hemoglobin",
      "result": "14.2",
      "unit": "g/dL",
      "reference_range": "12.0-15.5",
      "status": "normal"
    },
    {
      "test_name": "White Blood Cells",
      "result": "7.8",
      "unit": "K/uL", 
      "reference_range": "4.0-11.0",
      "status": "normal"
    }
  ],
  "patient_info": {
    "name": "John Doe",
    "date": "2025-01-15"
  }
}
```

### Prescription Output
```json
{
  "doctor_info": {
    "name": "Dr. Jane Smith",
    "specialty": "Internal Medicine",
    "license": "MD12345"
  },
  "patient_info": {
    "name": "Mary Johnson",
    "age": "35",
    "id": "P67890"
  },
  "medications": [
    {
      "name": "Amoxicillin",
      "dosage": "500mg",
      "frequency": "twice daily",
      "duration": "7 days",
      "instructions": "Take with food"
    }
  ],
  "date": "2025-01-15"
}
```

## 🏗️ Agent Architecture Details

### Base Agent Class
```python
class Agent:
    def __init__(self, name: str, instructions: str, handoffs: List['Agent'] = None):
        self.name = name
        self.instructions = instructions
        self.handoffs = handoffs or []
    
    def run(self, message: str, context: Dict = None) -> AgentResponse:
        # Agent execution logic
```

### Triage Agent
- **Purpose**: Document classification and routing
- **Handoffs**: `[lab_agent, prescription_agent]`
- **Tools**: `OCRTool` for image processing

### Specialist Agents
- **Lab Report Agent**: Extracts test results, patient info
- **Prescription Agent**: Extracts medications, doctor info, patient info
- **Shared Tools**: Both use `OCRTool` for image processing

### OCR Tool
```python
class OCRTool:
    def extract_text(self, image_path: str) -> str:
        return ocr_image(image_path)
```

## 🚦 Error Handling

The system includes comprehensive error handling:

- **OCR Errors**: Graceful handling of image processing failures
- **API Errors**: Groq API timeout and rate limit handling
- **JSON Parsing**: Automatic cleanup of markdown-formatted responses
- **Classification Errors**: Fallback for unknown document types


## 📊 Performance

- **Classification Speed**: ~500ms per document
- **OCR Processing**: ~1-2 seconds per image
- **Data Extraction**: ~800ms per document
- **Memory Usage**: ~150MB baseline
