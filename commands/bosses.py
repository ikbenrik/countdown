import logging
import json
import os
import time
import discord
from discord.ext import commands

BOSSES_FILE = "bosses.json"

# ✅ Define duration parsing function
def parse_duration(time_str):
    """Parses time format (h/m/s) and converts to seconds."""
    duration_mapping = {"h": 3600, "m": 60, "s": 1}
    total_seconds = 0

    try:
        parts = time_str.lower().split()
        for part in parts:
            if part[-1] in duration_mapping and part[:-1].isdigit():
                total_seconds += int(part[:-1]) * duration_mapping[part[-1]]
            else:
                return None
    except ValueError:
        return None

    return total_seconds if total_seconds > 0 else None

def format_duration(seconds):
    """Converts seconds to hours and minutes (e.g., 3600 → '1h', 5400 → '1h 30m')"""
    hours = int(seconds) // 3600
    minutes = (int(seconds) % 3600) // 60

    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{minutes}m"

# ✅ Load bosses from file
def load_bosses():
    if not os.path.exists(BOSSES_FILE):
        return {}
    try:
        with open(BOSSES_FILE, "r") as file:
            data = json.load(file)
            for dungeon, bosses in data.items():
                for boss, duration in bosses.items():
                    if isinstance(duration, str):  # Fix incorrect storage format
                        data[dungeon][boss] = parse_duration(duration)
            return data
    except json.JSONDecodeError:
        logging.warning("⚠️ Failed to decode bosses.json! Resetting storage.")
        return {}

# ✅ Save bosses to file
def save_bosses(data):
    with open(BOSSES_FILE, "w") as file:
        json.dump(data, file, indent=4)

# ✅ Initialize boss storage
bosses_data = load_bosses()

async def find_boss(ctx, boss_name: str):
    """Finds a boss by name and creates an event for it."""
    boss_name = boss_name.lower().strip()

    for dungeon, bosses in bosses_data.items():
        if boss_name in bosses:
            duration = bosses[boss_name]
            current_time = int(time.time())
            countdown_time = current_time + int(duration)

            countdown_text = (
                f"🔴 **{boss_name.capitalize()}** 🔴\n"
                f"👤 **Posted by: {ctx.author.display_name}**\n"
                f"⏳ **Next spawn at** <t:{countdown_time}:F>\n"
                f"⏳ **Countdown:** <t:{countdown_time}:R>\n"
                f"⏳ **Interval:** {format_duration(duration)}"
            )

            message = await ctx.send(countdown_text)
            await message.add_reaction("✅")  # Reset event
            await message.add_reaction("🗑️")  # Delete event
            await message.add_reaction("🔔")  # Ping reaction

            try:
                await ctx.message.delete()  # ✅ Delete the user command after execution
            except discord.NotFound:
                logging.warning("⚠️ Command message was already deleted.")
            except discord.Forbidden:
                logging.warning("🚫 Bot does not have permission to delete messages in this channel!")

            return

    # ✅ If boss was not found
    error_msg = await ctx.send(f"❌ **Boss `{boss_name.capitalize()}` not found!** Use `!b add <dungeon> <boss> <time>` to add it.")
    await error_msg.add_reaction("🗑️")

async def get_bosses(ctx, dungeon: str):
    """Creates countdown events for all bosses inside a dungeon."""
    dungeon = dungeon.lower().strip()

    if dungeon not in bosses_data:
        error_msg = await ctx.send(f"❌ **Dungeon `{dungeon.capitalize()}` not found!** Use `!b add {dungeon}` to create it.")
        await error_msg.add_reaction("🗑️")
        return

    if not bosses_data[dungeon]:
        error_msg = await ctx.send(f"🏰 **{dungeon.capitalize()}** has no bosses added yet!")
        await error_msg.add_reaction("🗑️")
        return

    current_time = int(time.time())

    for boss, duration in bosses_data[dungeon].items():
        countdown_time = current_time + int(duration)

        countdown_text = (
            f"🔴 **{boss.capitalize()}** 🔴\n"
            f"👤 **Posted by: {ctx.author.display_name}**\n"
            f"⏳ **Next spawn at** <t:{countdown_time}:F>\n"
            f"⏳ **Countdown:** <t:{countdown_time}:R>\n"
            f"⏳ **Interval:** {format_duration(duration)}"
        )

        message = await ctx.send(countdown_text)
        await message.add_reaction("✅")  
        await message.add_reaction("🗑️")  
        await message.add_reaction("🔔")  

    try:
        await ctx.message.delete()  
    except discord.NotFound:
        logging.warning("⚠️ Command message was already deleted.")
    except discord.Forbidden:
        logging.warning("🚫 Bot does not have permission to delete messages in this channel!")

async def list_all_bosses(ctx):
    """Lists all dungeons and their bosses."""
    bosses_data = load_bosses()

    if not bosses_data:
        response = await ctx.send("📜 **No dungeons or bosses stored!** Use `!b add <dungeon>` to start adding.")
        await response.add_reaction("🗑️")
        return

    dungeon_list = []
    for dungeon, bosses in bosses_data.items():
        boss_entries = "\n".join(
            f"  🔴 **{boss.capitalize()}** - {format_duration(duration)}"
            for boss, duration in bosses.items()
        ) if bosses else "  ❌ No bosses added yet!"

        dungeon_list.append(f"🏰 **{dungeon.capitalize()}**\n{boss_entries}")

    formatted_list = "\n\n".join(dungeon_list)
    response = await ctx.send(f"📜 **Dungeons & Bosses:**\n{formatted_list}")
    await response.add_reaction("🗑️")
