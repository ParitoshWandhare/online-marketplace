# genai-services/src/vision_ai/processors/image_processor.py
from PIL import Image
import io

def preprocess_image(image_bytes: bytes) -> bytes:
    try:
        # Open and validate image
        img = Image.open(io.BytesIO(image_bytes))
        detected_format = img.format if img.format else "Unknown"
        if detected_format not in ["JPEG", "PNG", "WEBP"]:
            img = img.convert("RGB")  # Convert WEBP to RGB
        
        # Resize to 512x512 for consistency
        img = img.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
        
        # Save back to bytes
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        return buffered.getvalue()
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")