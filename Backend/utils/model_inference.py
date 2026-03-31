import os

MODEL = None

def load_model():
    global MODEL

    if MODEL is not None:
        return MODEL

    try:
        from ultralytics import YOLO

        model_path = os.path.join("model", "best.pt")  # change if needed

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        MODEL = YOLO(model_path)
        print(f"✅ YOLO model loaded from {model_path}")
        return MODEL

    except Exception as e:
        print(f"❌ MODEL LOAD ERROR: {e}")
        return None


def map_to_dashboard_category(label: str) -> str:
    label = label.lower().strip()

    plastic_keywords = ["plastic", "bottle", "wrapper", "packet", "container"]
    paper_keywords = ["paper", "cardboard", "carton", "newspaper", "cup"]
    organic_keywords = ["organic", "food", "banana", "fruit", "vegetable", "peel"]
    metal_keywords = ["metal", "can", "tin", "aluminium", "aluminum", "steel"]

    if any(word in label for word in plastic_keywords):
        return "Plastic"
    elif any(word in label for word in paper_keywords):
        return "Paper"
    elif any(word in label for word in organic_keywords):
        return "Organic"
    elif any(word in label for word in metal_keywords):
        return "Metal"
    else:
        return "Other"


def predict_waste(image_path: str) -> dict:
    try:
        model = load_model()

        if model is None:
            return {
                "rawLabel": "Unknown",
                "label": "Other",
                "confidence": 0.0,
                "error": "Model failed to load"
            }

        results = model(image_path)
        result = results[0]

        # ===== CLASSIFICATION MODEL LOGIC =====
        if result.probs is not None:
            top1_index = int(result.probs.top1)
            confidence = float(result.probs.top1conf.item())
            raw_label = result.names[top1_index]
            mapped_label = map_to_dashboard_category(raw_label)

            return {
                "rawLabel": raw_label,
                "label": mapped_label,
                "confidence": round(confidence, 2)
            }

        # ===== DETECTION MODEL FALLBACK =====
        if result.boxes is not None and len(result.boxes) > 0:
            best_box = result.boxes[0]
            class_id = int(best_box.cls[0].item())
            confidence = float(best_box.conf[0].item())
            raw_label = result.names[class_id]
            mapped_label = map_to_dashboard_category(raw_label)

            return {
                "rawLabel": raw_label,
                "label": mapped_label,
                "confidence": round(confidence, 2)
            }

        return {
            "rawLabel": "Unknown",
            "label": "Other",
            "confidence": 0.0,
            "error": "No waste detected"
        }

    except Exception as e:
        print(f"❌ PREDICTION ERROR: {e}")
        return {
            "rawLabel": "Unknown",
            "label": "Other",
            "confidence": 0.0,
            "error": str(e)
        }