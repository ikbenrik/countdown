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

    # ✅ Delete the user's command message
    try:
        await ctx.message.delete()
    except discord.NotFound:
        logging.warning("⚠️ Warning: Command message was already deleted.")

async def list_items(ctx):
    """Displays all stored items and their durations, splitting into multiple messages if needed."""
    global item_timers
    item_timers = load_items()  # ✅ Reload the latest data

    if not item_timers:
        response = await ctx.send("📜 **No items stored!** Use `!add <item> <duration>` to store one.")
        await response.add_reaction("🗑️")  # ✅ Trash bin reaction
        return

    unique_items = {}  # ✅ Dictionary to store unique items
    for item, seconds in item_timers.items():
        item_name = item.strip().lower().capitalize()  # ✅ Normalize case & remove extra spaces
        if item_name in unique_items:
            continue  # ✅ Skip duplicates
        unique_items[item_name] = seconds  # ✅ Store only unique items

    message_chunks = []  # ✅ List to store message parts
    current_chunk = "📜 **Stored Items:**\n"  # ✅ Start with a header

    for item, seconds in unique_items.items():
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        # ✅ Only show minutes if nonzero
        if hours > 0 and minutes > 0:
            duration_str = f"{hours}h {minutes}m"
        elif hours > 0:
            duration_str = f"{hours}h"
        else:
            duration_str = f"{minutes}m"

        entry = f"🔹 **{item}** - {duration_str}\n"

        # ✅ If adding this entry exceeds 2000 characters, store the current chunk and start a new one
        if len(current_chunk) + len(entry) > 2000:
            message_chunks.append(current_chunk)
            current_chunk = "📜 **Stored Items (contd.):**\n" + entry  # ✅ Start a new chunk
        else:
            current_chunk += entry

    # ✅ Add the last chunk
    if current_chunk:
        message_chunks.append(current_chunk)

    sent_messages = []  # ✅ Store sent messages for bulk deletion

    # ✅ Send each chunk as a separate message
    for chunk in message_chunks:
        msg = await ctx.send(chunk)
        sent_messages.append(msg)

    # ✅ Add a 🗑️ reaction to the last message for bulk deletion
    if sent_messages:
        await sent_messages[-1].add_reaction("🗑️")

    # ✅ Store the messages for deletion handling
    bot = ctx.bot
    bot.list_messages_to_delete = sent_messages

    # ✅ Delete the user's command message
    try:
        await ctx.message.delete()
    except discord.NotFound:
        logging.warning("⚠️ Warning: Command message was already deleted.")
