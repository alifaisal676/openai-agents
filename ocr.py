from PIL import Image
import pytesseract

def ocr_image(image_path: str) -> str:
    """
    Takes an image file path and returns extracted text.
    """
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text.strip()

# ocr_image("input-image.png")
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(ocr_image("sample_images/prescription_sample.png"))

