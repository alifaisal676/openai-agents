from pathlib import Path
import logging

from .config import SUPPORTED_EXTENSIONS, OCR_SUBDIR

logger = logging.getLogger(__name__)

def find_lab_images(directory: Path) -> list:
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    images = [
        f for f in directory.glob('*') 
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(images)



def is_already_processed(image_path: Path, output_dir: Path) -> bool:
    stem = image_path.stem
    
    json_file = output_dir / f"{stem}_structured.json"
    ocr_file = output_dir / OCR_SUBDIR / f"{stem}_ocr.txt"
    if json_file.exists() and ocr_file.exists():
        logger.info(f"Skipping {stem} - already processed")
        return True
    return False



def setup_output_directory(output_dir: Path):
    output_dir.mkdir(exist_ok=True)
    (output_dir / OCR_SUBDIR).mkdir(exist_ok=True)
    
    

def get_output_filename(image_path: Path, output_dir: Path) -> Path:
    return output_dir / f"{image_path.stem}_structured.json"
