import logging
import json
import os
import discord

ITEMS_FILE = "items.json"

# ✅ Load items from file
def load_items():
    """Loads items from JSON file."""
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
    """Saves items to JSON file."""
    with open(ITEMS_FILE, "w") as file:
        json.dump(data, file, indent=4)

# ✅ Initialize items storage
item_timers = load_items()

async def add_item(ctx, item_name: str, duration_str: str):
    """Adds a new item with a duration in hours/minutes."""
    item_name = item_name.lower().strip()
    logging.debug(f"📌 User {ctx.author} requested to add item: {item_name} with duration {duration_str}")

    duration_mapping = {"h": 3600, "m": 60}

    try:
        duration = sum(
            int(value[:-1]) * duration_mapping[value[-1]]
            for value in duration_str.split()
            if value[-1] in duration_mapping and value[:-1].isdigit()
        )
    except ValueError:
        response = await ctx.send("❌ **Invalid time format!** Use `h/m` (e.g., `1h 30m`).")
        await response.add_reaction("🗑️")
        return

    # ✅ Save to JSON
    item_timers[item_name] = duration
    save_items(item_timers)  # **Missing in your previous code!**

    hours = duration // 3600
    minutes = (duration % 3600) // 60
    duration_text = f"{hours}h {minutes}m" if minutes else f"{hours}h"

    logging.info(f"✅ Added item: {item_name} with duration {duration_text}")
    response = await ctx.send(f"✅ **Added:** {item_name.capitalize()} - {duration_text}")
    await response.add_reaction("🗑️")

async def remove_item(ctx, item_name: str):
    """Removes an item from the list."""
    item_name = item_name.lower().strip()

    if item_name in item_timers:
        del item_timers[item_name]
        save_items(item_timers)  # **Make sure the item is removed from storage!**

        response = await ctx.send(f"🗑️ **Removed:** {item_name.capitalize()}")
        await response.add_reaction("🗑️")
    else:
        response = await ctx.send(f"⚠️ **Item not found:** {item_name.capitalize()}")
        await response.add_reaction("🗑️")
