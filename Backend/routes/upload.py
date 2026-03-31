print("🔥 upload.py loaded")

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import shutil
from datetime import datetime

from controllers.waste_controller import add_waste_entry

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-event")
async def upload_event(
    binId: str = Form(...),
    fillLevel: int = Form(...),
    wasteType: str = Form(...),
    image: UploadFile = File(...)
):
    print("📸 /api/upload-event HIT")

    if not binId or fillLevel is None or not wasteType:
        raise HTTPException(status_code=400, detail="binId, wasteType, and fillLevel are required")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_name = image.filename.replace(" ", "_")
    filename = f"{binId}_{timestamp}_{safe_name}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_url = f"/uploads/{filename}"

    result = add_waste_entry(
        bin_id=binId,
        waste_type=wasteType,
        fill_level=fillLevel,
        image_url=image_url
    )

    return {
        "message": "Image uploaded and waste event stored successfully",
        "imageUrl": image_url,
        "data": result
    }