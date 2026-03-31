import json
import os

# Always point to Backend/data.json safely
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data.json")


def load_data():
    try:
        if not os.path.exists(DATA_FILE):
            default_data = {"bins": [], "logs": []}
            save_data(default_data)
            return default_data

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()

            if not content:
                default_data = {"bins": [], "logs": []}
                save_data(default_data)
                return default_data

            return json.loads(content)

    except Exception as e:
        print(f"❌ load_data ERROR: {e}")
        return {"bins": [], "logs": []}


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"❌ save_data ERROR: {e}")
        raise