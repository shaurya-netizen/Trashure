import random
import os


def classify_waste(image_filename: str) -> dict:
    """
    Temporary fake classifier.
    Later this will be replaced by your real ML model.
    """

    filename = os.path.basename(image_filename).lower()

    if "plastic" in filename:
        label = "Plastic"
        confidence = 0.95
    elif "paper" in filename:
        label = "Paper"
        confidence = 0.93
    elif "organic" in filename or "food" in filename:
        label = "Organic"
        confidence = 0.94
    else:
        label = random.choice(["Plastic", "Paper", "Organic"])
        confidence = round(random.uniform(0.80, 0.96), 2)

    return {
        "label": label,
        "confidence": confidence
    }