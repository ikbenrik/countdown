import logging
import json
import os

ITEMS_FILE = "items.json"

# ✅ Load items from file
def load_items():
    if not os.path.exists(ITEMS_FILE):
        return {}
    try:
        with open(ITEMS_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        logging.warning("⚠️ Failed to decode items.json! Resetting storage.")
        return {}

# ✅ Save items to file
def save_items(data):
    with open(ITEMS_FILE, "w") as file:
        json.dump(data, file, indent=4)

# ✅ Initialize items storage
item_timers = load_items()

async def add_item(ctx, item_name: str, duration: str):
    """Adds a new item with a duration."""
    logging.debug(f"📌 User {ctx.author} requested to add item: {item_name} with duration {duration}")
    
    # ✅ Ensure lowercase for consistency
    item_name = item_name.lower()

    duration_mapping = {"h": 3600, "m": 60, "s": 1}
    if duration[-1] in duration_mapping and duration[:-1].isdigit():
        duration_seconds = int(duration[:-1]) * duration_mapping[duration[-1]]
    else:
        await ctx.send("❌ **Invalid time format!** Use `h/m/s` (e.g., `30m`)")
        return

    # ✅ Update the stored list
    item_timers[item_name] = duration_seconds
    save_items(item_timers)

    logging.info(f"✅ Added item: {item_name} with duration {duration} ({duration_seconds} seconds)")
    await ctx.send(f"✅ **{item_name.capitalize()}** added with duration **{duration}**")

async def remove_item(ctx, item_name: str):
    """Removes an item from storage."""
    logging.debug(f"🗑️ User {ctx.author} requested to delete item: {item_name}")
    
    item_name = item_name.lower()

    if item_name in item_timers:
        del item_timers[item_name]
        save_items(item_timers)
        logging.info(f"🗑️ Removed item: {item_name}")
        await ctx.send(f"🗑️ **{item_name.capitalize()}** removed.")
    else:
        logging.warning(f"⚠️ Attempted to remove non-existent item: {item_name}")
        await ctx.send(f"⚠️ **{item_name.capitalize()}** does not exist!")

# Ensure item_timers is loaded
from utils.helpers import load_items
item_timers = load_items()

async def list_items(ctx):
    """Displays all stored items and their durations."""
    logging.debug(f"📜 User {ctx.author} requested the item list.")

    if not item_timers:
        await ctx.send("📭 **No items stored!** Use `!add <item> <time>` to add one.")
        return

    item_list = "\n".join([f"🔹 **{item.capitalize()}** - {seconds//60}m" for item, seconds in item_timers.items()])
    
    logging.info("📜 Sending item list.")
    await ctx.send(f"📜 **Stored Items:**\n{item_list}")

# ✅ Reload items on startup
item_timers = load_items()
