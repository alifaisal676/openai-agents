# 🚀 Lab Report Batch Processor

## 📋 Overview
This tool processes multiple lab report images in batch, extracting structured data using OCR and AI analysis.

## 🔧 Features
- ✅ **Batch Processing**: Handle multiple images at once
- ✅ **Organized Output**: Separate folders for structured data and OCR outputs
- ✅ **Progress Tracking**: Real-time processing status
- ✅ **Error Handling**: Continue processing even if some images fail
- ✅ **Summary Reports**: Detailed processing statistics
- ✅ **Performance Optimized**: ~4-5 seconds per image

## 📁 Output Structure
```
processed_reports/
├── image1_structured.json      # Structured lab data
├── image2_structured.json      # Structured lab data
├── ocr_outputs/                # Raw OCR text files
│   ├── image1_ocr.txt
│   └── image2_ocr.txt
└── processing_summary.json     # Batch processing summary
```

## 🚀 Usage

### Basic Usage
```bash
python batch_processor.py <input_folder>
```

### With Custom Output Folder
```bash
python batch_processor.py <input_folder> <output_folder>
```

### Examples
```bash
# Process all images in 'lab_images' folder
python batch_processor.py lab_images

# Process with custom output location
python batch_processor.py lab_images my_processed_reports

# Process images from different locations
python batch_processor.py "C:/Users/Documents/LabImages" "C:/Output"
```

## 📸 Supported Image Formats
- PNG, JPG, JPEG, TIFF, BMP, GIF
- Both lowercase and uppercase extensions

## 📊 Performance
- **Processing Speed**: ~4-5 seconds per image
- **Accuracy**: High accuracy with medical lab reports
- **Batch Size**: No limit (processes sequentially to avoid rate limits)

## 🔍 Output Files

### Structured JSON Output
Each processed image generates a JSON file with:
```json
{
  "patient_name": "John Doe",
  "age": "35 Years", 
  "gender": "Male",
  "doctor_name": "Dr. Smith",
  "date": "15 Jan, 2025",
  "comments": "",
  "test_results": [
    {
      "test_name": "Glucose",
      "value": "95",
      "unit": "mg/dL",
      "reference_range": "70-100"
    }
  ]
}
```

### Processing Summary
```json
{
  "processing_summary": {
    "total_images": 5,
    "successful": 4,
    "failed": 1,
    "total_duration": "23.5s",
    "average_per_image": "4.7s"
  },
  "successful_processes": [...],
  "failed_processes": [...]
}
```

## ⚠️ Requirements
- Python 3.8+
- OpenAI/Groq API key in .env file
- Required packages: `pip install openai python-dotenv pillow pytesseract pydantic`
- Tesseract OCR installed

## 🛠️ Troubleshooting
- **No images found**: Check image formats and folder path
- **API errors**: Verify .env file has correct GROQ_API_KEY
- **OCR errors**: Ensure Tesseract is installed and in PATH
- **Rate limiting**: Tool includes automatic delays between requests

## 🎯 Best Practices
1. **Organize Input**: Place all lab report images in one folder
2. **Check Output**: Review processing_summary.json for any failures
3. **Backup Data**: Keep original images as backup
4. **Monitor Performance**: Check logs for processing times and errors
