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
            data = json.load(file)
            # ✅ Convert all times from string to integer (if stored incorrectly)
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

    # ✅ Check if boss already exists
    if boss_name in bosses_data[dungeon]:
        confirmation_msg = await ctx.send(f"⚠️ **Boss `{boss_name.capitalize()}` already exists in `{dungeon.capitalize()}`!**\nDo you want to overwrite the timer? React with 👍 to confirm, or 👎 to cancel.")
        await confirmation_msg.add_reaction("👍")
        await confirmation_msg.add_reaction("👎")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["👍", "👎"]

        try:
            reaction, _ = await ctx.bot.wait_for("reaction_add", timeout=30.0, check=check)
            if str(reaction.emoji) == "👍":
                bosses_data[dungeon][boss_name] = duration  
                save_bosses(bosses_data)
                await ctx.send(f"✅ **Updated `{boss_name.capitalize()}` timer to {format_duration(duration)}!**")
            else:
                await ctx.send("❌ **Boss timer update cancelled.**")
            return
        except TimeoutError:
            await ctx.send("⌛ **Boss overwrite request timed out.**")
            return

    bosses_data[dungeon][boss_name] = duration
    save_bosses(bosses_data)

    await ctx.send(f"🔴 **Added Boss:** `{boss_name.capitalize()}` in `{dungeon.capitalize()}` with a timer of `{format_duration(duration)}`.")

async def find_boss(ctx, boss_name: str):
    """Creates a countdown event for a single boss."""
    boss_name = boss_name.lower().strip()
    current_time = int(time.time())

    for dungeon, bosses in bosses_data.items():
        if boss_name in bosses:
            duration = int(bosses[boss_name])
            countdown_time = current_time + duration

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

            try:
                await ctx.message.delete()  
            except discord.NotFound:
                logging.warning("⚠️ Command message was already deleted.")
            return True

    error_msg = await ctx.send(f"❌ **Boss `{boss_name.capitalize()}` not found!** Use `!b list` to check available bosses.")
    await error_msg.add_reaction("🗑️")
    return False
