"""
Configuration and constants for lab report processing.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL_NAME = "llama3-70b-8192"
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY=os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT="LabReportAgentTrace"



# Processing Configuration
MAX_TOKENS = 800
TIMEOUT = 10
TEMPERATURE = 0.1
MAX_ITERATIONS = 3

# File Configuration
SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
OCR_SUBDIR = "ocr_outputs"

# Prompts
SYSTEM_PROMPT = """You are a medical lab report processor. You have these tools:
1. extract_text - OCR from images
2. structure_data - Convert text to JSON
3. validate_data - Check data quality

Process efficiently: extract → structure → validate. Use each tool once."""

STRUCTURE_PROMPT = """Extract lab report data as JSON with these fields:
- patient_name, age, gender, doctor_name, date, comments
- test_results (array): test_name, value, unit, reference_range

Keep values as strings for qualitative results. Use empty strings for missing data.
Return only valid JSON."""
