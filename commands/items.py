import logging
import json
import os
import asyncio  # Needed for delayed deletion
from utils.helpers import load_items

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

async def add_item(ctx, item_name: str, duration_str: str):
    """Adds a new item with a duration in hours/minutes."""
    duration_mapping = {"h": 3600, "m": 60}
    duration = sum(int(value[:-1]) * duration_mapping[value[-1]] for value in duration_str.split() if value[-1] in duration_mapping)

    item_timers[item_name.lower()] = duration
    logging.info(f"✅ Added item: {item_name} with duration {duration // 3600}h {duration % 3600 // 60}m")

    response = await ctx.send(f"✅ **Added:** {item_name.capitalize()} - {duration // 3600}h {duration % 3600 // 60}m")
    await response.add_reaction("🗑️")  # 🗑️ Trash Can for Deletion

    try:
        await ctx.message.delete()  # ✅ Delete user command after execution
    except discord.NotFound:
        print("⚠️ Warning: Command message was already deleted.")


async def remove_item(ctx, item_name: str):
    """Removes an item from the list."""
    if item_name.lower() in item_timers:
        del item_timers[item_name.lower()]
        logging.info(f"🗑️ Removed item: {item_name}")

        response = await ctx.send(f"🗑️ **Removed:** {item_name.capitalize()}")
        await response.add_reaction("🗑️")  # 🗑️ Trash Can for Deletion
    else:
        logging.warning(f"⚠️ Attempted to remove non-existent item: {item_name}")
        response = await ctx.send(f"⚠️ **Item not found:** {item_name.capitalize()}")
        await response.add_reaction("🗑️")  # 🗑️ Trash Can for Deletion

# ✅ Reload items on startup
item_timers = load_items()
