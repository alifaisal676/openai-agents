# Prescription Processing Pipeline

A Python tool that extracts medicine information from prescription images using Azure OCR and AI models.

## Features

- **Image Enhancement**: Improves prescription image quality for better OCR
- **Azure OCR Integration**: Extracts text from prescription images
- **Dual AI Support**: Choose between BioGPT (local) or LLaMA (API)
- **Medicine Validation**: Matches extracted medicines against known database
- **Anti-Hallucination**: BioGPT mode uses OCR-only extraction to prevent false results

## Quick Start

1. **Install Dependencies**
```bash
pip install opencv-python requests rapidfuzz python-dotenv openai transformers torch
```

2. **Setup Environment**
Create `.env` file:
```env
AZURE_OCR_ENDPOINT=your_azure_endpoint
AZURE_OCR_KEY=your_azure_key
GROQ_API_KEY=your_groq_key  # Only for LLaMA
```

3. **Run**
```bash
python simple_pipeline.py
```

## Usage

Place your prescription image as `pic.jpg` in the project folder. The tool will:
- Enhance image quality
- Extract text using Azure OCR
- Find medicine names using AI
- Validate against medicine database
- Save results to `outputs/` folder

## Model Options

**BioGPT** (Recommended)
- Runs locally
- Medical-specific AI
- No hallucinations
- Requires: Azure OCR only

**LLaMA**
- Cloud-based via Groq
- General AI model
- JSON output
- Requires: Azure OCR + Groq API

Change model in `main()`:
```python
model = "biogpt"  # or "llama"
```

## Output Files

- `ocr_raw.txt` - Raw OCR text
- `ocr_cleaned.txt` - Cleaned text
- `output_raw.json` - Extracted medicines
- `output_validated.json` - Validated results with confidence scores

## Requirements

- Python 3.7+
- Azure Computer Vision API
- Groq API (for LLaMA only)
- `medicines.js` database file

## Example Output

```json
[
  {
    "medicine": "Paracetamol",
    "dosage": "500mg",
    "frequency": "BD",
    "confidence": 95
  }
]
```

## Notes

- BioGPT model downloads automatically on first run (~1.5GB)
- Supports various prescription formats
- Medicine validation uses fuzzy matching
- Anti-hallucination measures prevent false medicine detection

## License

MIT License
