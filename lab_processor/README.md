# Lab Processor - Modular Package

A clean, modular system for processing lab report images into structured JSON data.

## Structure

```
lab_processor/
├── __init__.py          # Package initialization
├── config.py            # Configuration and constants
├── models.py            # Data models and validation
├── tools.py             # Core processing functions (OCR, LLM, validation)
├── agent.py             # Agent-based processor for individual reports
├── utils.py             # File utilities and duplicate detection
└── batch.py             # Batch processing logic
```

## Usage

### New Clean Interface
```python
from lab_processor.batch import BatchProcessor

processor = BatchProcessor()
results = processor.process_directory("input_dir", "output_dir")
```

### Command Line
```bash
python batch_processor_clean.py
```

### Legacy Interface (backward compatibility)
```python
from batch_processor import batch_process_lab_reports

results = batch_process_lab_reports("input_dir", "output_dir")
```

## Features

- **Modular Design**: Each component has a single responsibility
- **Clean Code**: No AI-generated comments or verbose documentation
- **Agent-Based**: Uses OpenAI SDK with tool calling for reliable processing
- **Duplicate Detection**: Skips already processed files
- **Error Handling**: Graceful failure recovery
- **Progress Tracking**: Real-time processing status

## Configuration

Set up your `.env` file:
```
GROQ_API_KEY=your_api_key_here
```

## Output

- Structured JSON files in `{output_dir}/{image}_structured.json`
- OCR text files in `{output_dir}/ocr_outputs/{image}_ocr.txt`
- Processing summary in `{output_dir}/processing_summary.json`
