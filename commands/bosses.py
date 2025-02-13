import logging
import json
import os
import time
import discord
from discord.ext import commands

BOSSES_FILE = "bosses.json"

# ✅ Load bosses from file
def load_bosses():
    if not os.path.exists(BOSSES_FILE):
        return {}
    try:
        with open(BOSSES_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        logging.warning("⚠️ Failed to decode bosses.json! Resetting storage.")
        return {}

# ✅ Save bosses to file
def save_bosses(data):
    with open(BOSSES_FILE, "w") as file:
        json.dump(data, file, indent=4)

# ✅ Initialize boss storage
bosses_data = load_bosses()

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

async def add_boss(ctx, dungeon: str, boss_name: str = None, time: str = None):
    """Adds a dungeon or a boss with a timer inside a dungeon."""
    dungeon = dungeon.lower().strip()

    if dungeon not in bosses_data:
        bosses_data[dungeon] = {}  # ✅ Create dungeon if it doesn't exist
        save_bosses(bosses_data)
        await ctx.send(f"🏰 **Added Dungeon:** `{dungeon.capitalize()}`")
        return

    if not boss_name or not time:
        error_msg = await ctx.send("❌ **You must specify both a boss name and a time!** Use `!b add <dungeon> <boss> <time>`.")
        await error_msg.add_reaction("🗑️")
        return

    boss_name = boss_name.lower().strip()
    duration = parse_duration(time)
    if duration is None:
        error_msg = await ctx.send("❌ **Invalid time format!** Use `h/m/s` (e.g., `1h 30m`, `3000s`).")
        await error_msg.add_reaction("🗑️")
        return

    bosses_data[dungeon][boss_name] = duration
    save_bosses(bosses_data)

    await ctx.send(f"🔴 **Added Boss:** `{boss_name.capitalize()}` in `{dungeon.capitalize()}` with a timer of `{format_duration(duration)}`.")

async def get_bosses(ctx, dungeon: str):
    """Creates countdown events for all bosses inside a dungeon."""
    dungeon = dungeon.lower().strip()

    if dungeon not in bosses_data:
        error_msg = await ctx.send(f"❌ **Dungeon `{dungeon.capitalize()}` not found!** Use `!b add {dungeon}` to create it.")
        await error_msg.add_reaction("🗑️")
        return

    if not bosses_data[dungeon]:
        error_msg = await ctx.send(f"🏰 **{dungeon.capitalize()}** has no bosses added yet! Use `!b add {dungeon} <boss> <time>`.")
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

async def find_boss(ctx, boss_name: str):
    """Finds and creates an event for a boss, even if the dungeon is not specified."""
    boss_name = boss_name.lower().strip()

    for dungeon, bosses in bosses_data.items():
        if boss_name in bosses:
            duration = bosses[boss_name]
            countdown_time = int(time.time()) + int(duration)

            countdown_text = (
                f"🔴 **{boss_name.capitalize()}** 🔴\n"
                f"👤 **Posted by: {ctx.author.display_name}**\n"
                f"⏳ **Next spawn at** <t:{countdown_time}:F>\n"
                f"⏳ **Countdown:** <t:{countdown_time}:R>\n"
                f"⏳ **Interval:** {format_duration(duration)}"
            )

            message = await ctx.send(countdown_text)
            await message.add_reaction("✅")  
            await message.add_reaction("🗑️")  
            await message.add_reaction("🔔")  

            return True  

    error_msg = await ctx.send(f"❌ **Boss `{boss_name.capitalize()}` not found!** Try `!b list` to see all bosses.")
    await error_msg.add_reaction("🗑️")
    return False  
