from datetime import datetime
import random

from utils.file_db import load_data, save_data


def get_status(fill_level: int):
    if fill_level >= 85:
        return "Full"
    elif fill_level >= 50:
        return "Filling"
    return "Normal"


# =========================
# READ FUNCTIONS
# =========================

def get_bins():
    try:
        data = load_data()
        return {"bins": data.get("bins", [])}
    except Exception as e:
        print(f"❌ get_bins ERROR: {e}")
        return {"bins": []}


def get_logs():
    try:
        data = load_data()
        return {"logs": data.get("logs", [])}
    except Exception as e:
        print(f"❌ get_logs ERROR: {e}")
        return {"logs": []}


# =========================
# MAIN WASTE EVENT FUNCTION
# =========================

def add_waste_entry(bin_id: str, waste_type: str, fill_level: int, image_url: str = ""):
    try:
        data = load_data()
        bins = data.get("bins", [])
        logs = data.get("logs", [])

        current_time = datetime.now().strftime("%I:%M %p")
        timestamp = datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p")

        # Find existing bin
        bin_found = None
        for bin_obj in bins:
            if bin_obj["id"] == bin_id:
                bin_found = bin_obj
                break

        if bin_found:
            bin_found["entries"] += 1
            bin_found["waste"] = waste_type
            bin_found["fill"] = fill_level
            bin_found["last"] = current_time
            bin_found["status"] = get_status(fill_level)
            bin_found["imageUrl"] = image_url
        else:
            bin_found = {
                "id": bin_id,
                "location": "Unknown Location",
                "entries": 1,
                "waste": waste_type,
                "fill": fill_level,
                "last": current_time,
                "status": get_status(fill_level),
                "imageUrl": image_url
            }
            bins.append(bin_found)

        logs.append({
            "binId": bin_id,
            "wasteType": waste_type,
            "fillLevel": fill_level,
            "imageUrl": image_url,
            "timestamp": timestamp
        })

        data["bins"] = bins
        data["logs"] = logs
        save_data(data)

        return {
            "message": "Waste data stored successfully",
            "bin": bin_found
        }

    except Exception as e:
        print(f"❌ add_waste_entry ERROR: {e}")
        raise


# =========================
# RESET FUNCTION
# =========================

def reset_data():
    try:
        data = {
            "bins": [],
            "logs": []
        }
        save_data(data)
        return {"message": "All data reset successfully"}
    except Exception as e:
        print(f"❌ reset_data ERROR: {e}")
        raise


# =========================
# SIMULATE FUNCTION
# =========================

def simulate_event():
    try:
        data = load_data()
        bins = data.get("bins", [])

        if not bins:
            return {"message": "No bins available to simulate"}

        chosen_bin = random.choice(bins)
        waste_type = random.choice(["Plastic", "Paper", "Organic"])
        new_fill = min(100, chosen_bin["fill"] + random.randint(5, 20))

        result = add_waste_entry(
            bin_id=chosen_bin["id"],
            waste_type=waste_type,
            fill_level=new_fill,
            image_url=chosen_bin.get("imageUrl", "")
        )

        return {
            "message": "Simulation successful",
            "data": result
        }

    except Exception as e:
        print(f"❌ simulate_event ERROR: {e}")
        raise