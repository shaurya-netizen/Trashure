from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import shutil
from datetime import datetime

from utils.file_db import load_data
from utils.image_compare import images_are_different
from controllers.waste_controller import add_waste_entry

# later we’ll replace this import with real model
from utils.model_inference import predict_waste

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/process-event")
async def process_event(
    binId: str = Form(...),
    fillLevel: int = Form(...),
    image: UploadFile = File(...)
):
    try:
        if not binId or fillLevel is None:
            raise HTTPException(status_code=400, detail="binId and fillLevel are required")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{binId}_{timestamp}_{image.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save uploaded image
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        image_url = f"/uploads/{filename}"

        # Load current data
        data = load_data()
        bins = data.get("bins", [])

        # Find last image for this bin
        last_image_path = None
        for bin_obj in bins:
            if bin_obj.get("id") == binId and bin_obj.get("imageUrl"):
                last_image_path = bin_obj["imageUrl"].replace("/uploads/", "uploads/")
                break

        # Compare with last image
        if last_image_path and os.path.exists(last_image_path):
            changed = images_are_different(file_path, last_image_path, threshold=8.0)
        else:
            changed = True  # first image for bin

        if not changed:
            print("🟡 No meaningful change detected. Ignoring event.")
            if os.path.exists(file_path):
                os.remove(file_path)

            return {
                "message": "No meaningful change detected. Event ignored.",
                "changeDetected": False
            }

        print("🟢 Change detected. Running classification...")

        prediction = predict_waste(file_path)
        print("🤖 Prediction:", prediction)

        predicted_waste = prediction["label"]
        raw_label = prediction["rawLabel"]
        confidence = prediction["confidence"]

        if predicted_waste == "Unknown":
            return {
        "message": "Change detected, but classification failed",
        "changeDetected": True,
        "predictedWaste": predicted_waste,
        "confidence": confidence,
        "error": prediction.get("error", "Unknown model error")
    }

        print("💾 Saving event...")

        result = add_waste_entry(
            bin_id=binId,
            waste_type=predicted_waste,
            fill_level=fillLevel,
            image_url=image_url
        )

        print("✅ Event saved successfully")

        return {
            "message": "New waste event processed successfully",
            "changeDetected": True,
            "predictedWaste": predicted_waste,
            "rawLabel": raw_label,
            "confidence": confidence,
            "imageUrl": image_url,
            "data": result
}

    except Exception as e:
        print("❌ PROCESS EVENT ERROR:", str(e))
        raise HTTPException(status_code=500, detail=f"Process event failed: {str(e)}")