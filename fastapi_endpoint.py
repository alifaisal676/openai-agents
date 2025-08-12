
import io
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image

from lab_processor.agent import LabReportAgent


app = FastAPI(
    title="Lab Report Processing API",
    description="Process lab report images and extract structured data",
    version="1.0.0"
)

# Initialize the agent
agent = LabReportAgent()


@app.post("/process-lab-report", response_model=Dict[str, Any])
async def process_lab_report(file: UploadFile = File(...)):
  
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400, 
            detail="File must be an image (PNG, JPG, JPEG, TIFF, BMP)"
        )
    
    # Check file extension
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Read and validate image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
            image.save(temp_file.name)
            temp_image_path = temp_file.name
        
        # Create temporary output file path
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_output:
            temp_output_path = temp_output.name
        
        try:
            # Process the image using the agent
            result = agent.process_image(temp_image_path, temp_output_path)
            
            if result["status"] == "success":
                # Return the structured data
                return {
                    "status": "success",
                    "message": "Lab report processed successfully",
                    "filename": file.filename,
                    "patient_name": result.get("patient_name", "Unknown"),
                    "processing_time": result.get("duration", 0),
                    "data": result.get("data", {})
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Processing failed: {result.get('error', 'Unknown error')}"
                )
                
        finally:
            # Clean up temporary files
            try:
                Path(temp_image_path).unlink(missing_ok=True)
                Path(temp_output_path).unlink(missing_ok=True)
            except:
                pass  # Ignore cleanup errors
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Lab Report Processing API is running"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Lab Report Processing API",
        "docs": "/docs",
        "health": "/health",
        "process_endpoint": "/process-lab-report"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
