import json
import os

ITEMS_FILE = "items.json"

def load_items():
    """Load items from a JSON file."""
    if os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return {key.lower().strip(): value for key, value in data.items()}  
            except json.JSONDecodeError:
                print("❌ ERROR: Could not decode JSON file.")
                return {}
    else:
        print(f"❌ ERROR: {ITEMS_FILE} not found.")
    return {}
