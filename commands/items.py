import json
import os
import logging

# ✅ Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

ITEMS_FILE = "items.json"

# ✅ Load saved items
def load_items():
    """Loads item durations from a JSON file."""
    if os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, "r") as f:
            return json.load(f)
    return {}

# ✅ Save items back to the file
def save_items(items):
    """Saves item durations to a JSON file."""
    with open(ITEMS_FILE, "w") as f:
        json.dump(items, f, indent=4)

# ✅ In-memory storage (used during runtime)
item_timers = load_items()

async def add_item(ctx, item_name: str, duration: str):
    """Adds a new item with a default duration."""
    logging.debug(f"📝 Received request to add item: {item_name} with duration {duration}")

    if not duration[:-1].isdigit() or duration[-1].lower() not in ["h", "m", "s"]:
        await ctx.send("❌ **Invalid format!** Time must end in `h`, `m`, or `s`. Example: `1h` or `30m`.")
        logging.warning(f"⚠️ Invalid time format entered: {duration}")
        return
    
    # Convert duration to seconds
    unit_map = {"h": 3600, "m": 60, "s": 1}
    duration_seconds = int(duration[:-1]) * unit_map[duration[-1].lower()]
    
    # Save the item
    item_timers[item_name.lower()] = duration_seconds
    save_items(item_timers)

    logging.info(f"✅ Added item: {item_name} with duration {duration} ({duration_seconds} seconds)")
    await ctx.send(f"✅ **{item_name.capitalize()}** added with a duration of `{duration}`.")

async def remove_item(ctx, item_name: str):
    """Removes an item from the storage."""
    item_name = item_name.lower()
    logging.debug(f"🗑️ Received request to remove item: {item_name}")

    if item_name in item_timers:
        del item_timers[item_name]
        save_items(item_timers)

        logging.info(f"🗑️ Removed item: {item_name}")
        await ctx.send(f"🗑️ **{item_name.capitalize()}** has been removed.")
    else:
        # ✅ Fix the unterminated f-string (missing closing quote)
        logging.warning(f"⚠️ Attempted to remove non-existent item: {item_name}")
