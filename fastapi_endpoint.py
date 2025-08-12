import asyncio
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from prescription_processor import process_prescription

app = FastAPI(title="Prescription Processing API", version="1.0.0")

@app.get('/')
def root():
    return {"message": "Prescription Processing API", "status": "active"}

@app.post('/process-prescription')
async def process_prescription_api(
    image: UploadFile = File(..., description="Prescription image file")
):
    """
    Process a prescription image and extract medicine information using LLaMA pipeline
    
    - **image**: Upload prescription image (jpg, png, etc.)
    
    Returns validated medicine data with LLM validation and database confidence scores
    """
    
    # Validate file type
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{image.filename}") as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Process the prescription with simplified pipeline
        result = await asyncio.to_thread(process_prescription, temp_path)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return JSONResponse(content={
            "success": True,
            "pipeline": "llama_extraction_and_validation",
            "medicines_count": len(result),
            "medicines": result
        })
        
    except Exception as e:
        # Clean up temp file in case of error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get('/health')
def health_check():
    return {"status": "healthy", "service": "prescription-processing"}
