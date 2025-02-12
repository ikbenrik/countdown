import logging
import json
import os
import discord
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

async def add_item(ctx, item_name: str, duration_str: str):
    """Adds a new item with a duration in hours/minutes."""
    logging.debug(f"📌 User {ctx.author} requested to add item: {item_name} with duration {duration_str}")

    item_name = item_name.lower()  # Normalize case
    duration_mapping = {"h": 3600, "m": 60}

    try:
        # ✅ Convert "1h 30m" into seconds
        duration = sum(
            int(value[:-1]) * duration_mapping[value[-1]]
            for value in duration_str.split()
            if value[-1] in duration_mapping and value[:-1].isdigit()
        )
    except ValueError:
        await ctx.send("❌ **Invalid time format!** Use `h/m` (e.g., `1h 30m`).")
        return

    # ✅ Store item with duration
    item_timers[item_name] = duration
    save_items(item_timers)

    hours = duration // 3600
    minutes = (duration % 3600) // 60

    # ✅ Only show minutes if nonzero
    if hours > 0 and minutes > 0:
        duration_text = f"{hours}h {minutes}m"
    elif hours > 0:
        duration_text = f"{hours}h"
    else:
        duration_text = f"{minutes}m"

    logging.info(f"✅ Added item: {item_name} with duration {duration_text}")
    response = await ctx.send(f"✅ **Added:** {item_name.capitalize()} - {duration_text}")
    await response.add_reaction("🗑️")  # 🗑️ Reaction for deletion

    try:
        await ctx.message.delete()  # ✅ Delete user command after execution
    except discord.NotFound:
        print("⚠️ Warning: Command message was already deleted.")

async def remove_item(ctx, item_name: str):
    """Removes an item from the list."""
    item_name = item_name.lower()

    if item_name in item_timers:
        del item_timers[item_name]
        save_items(item_timers)
        logging.info(f"🗑️ Removed item: {item_name}")

        response = await ctx.send(f"🗑️ **Removed:** {item_name.capitalize()}")
        await response.add_reaction("🗑️")  # 🗑️ Reaction for deletion
    else:
        logging.warning(f"⚠️ Attempted to remove non-existent item: {item_name}")
        response = await ctx.send(f"⚠️ **Item not found:** {item_name.capitalize()}")
        await response.add_reaction("🗑️")  # 🗑️ Reaction for deletion

async def list_items(ctx):
    """Displays all stored items and their durations."""
    item_timers = load_items()  # ✅ Reload latest data

    if not item_timers:
        response = await ctx.send("📜 **No items stored!** Use `!add <item> <duration>` to store one.")
        await response.add_reaction("🗑️")  # Allow deletion of bot message
        return

    formatted_items = []
    for item, seconds in item_timers.items():
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        # ✅ Only show minutes if nonzero
        if hours > 0 and minutes > 0:
            duration_str = f"{hours}h {minutes}m"
        elif hours > 0:
            duration_str = f"{hours}h"
        else:
            duration_str = f"{minutes}m"

        formatted_items.append(f"🔹 **{item.capitalize()}** - {duration_str}")

    item_list_message = "📜 **Stored Items:**\n" + "\n".join(formatted_items)
    response = await ctx.send(item_list_message)
    await response.add_reaction("🗑️")  # ✅ Reaction to delete message

    try:
        await ctx.message.delete()  # ✅ Delete user command after execution
    except discord.NotFound:
        print("⚠️ Warning: Command message was already deleted.")
