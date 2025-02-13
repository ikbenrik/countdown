import logging
import json
import os
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

async def add_boss(ctx, dungeon: str, boss_name: str = None, time: str = None):
    """Adds a dungeon or a boss with a timer inside a dungeon."""
    dungeon = dungeon.lower().strip()

    if dungeon not in bosses_data:
        bosses_data[dungeon] = {}  # ✅ Create dungeon if it doesn't exist
        save_bosses(bosses_data)
        await ctx.send(f"🏰 **Added Dungeon:** `{dungeon.capitalize()}`")
        return

    if not boss_name or not time:
        await ctx.send("❌ **You must specify both a boss name and a time!** Use `!b add <dungeon> <boss> <time>`.")
        return

    boss_name = boss_name.lower().strip()

    # ✅ Convert time format (Supports `h/m/s`)
    duration = parse_duration(time)
    if duration is None:
        await ctx.send("❌ **Invalid time format!** Use `h/m/s` (e.g., `1h 30m`, `3000s`).")
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

    # ✅ Store the boss inside the dungeon
    bosses_data[dungeon][boss_name] = duration
    save_bosses(bosses_data)

    await ctx.send(f"🔴 **Added Boss:** `{boss_name.capitalize()}` in `{dungeon.capitalize()}` with a timer of `{format_duration(duration)}`.")

async def get_bosses(ctx, dungeon: str):
    """Lists all bosses inside a dungeon."""
    dungeon = dungeon.lower().strip()

    if dungeon not in bosses_data:
        await ctx.send(f"❌ **Dungeon `{dungeon.capitalize()}` not found!** Use `!b add {dungeon}` to create it.")
        return

    if not bosses_data[dungeon]:
        await ctx.send(f"🏰 **{dungeon.capitalize()}** has no bosses added yet!")
        return

    boss_list = "\n".join(
        f"🔴 **{boss.capitalize()}** - {format_duration(time)}"
        for boss, time in bosses_data[dungeon].items()
    )
    await ctx.send(f"🏰 **{dungeon.capitalize()} Bosses:**\n{boss_list}")

async def list_all_bosses(ctx):
    """Displays all dungeons and their bosses with timers."""
    bosses_data = load_bosses()  # ✅ Reload latest data

    if not bosses_data:
        await ctx.send("❌ **No dungeons or bosses found!** Use `!b add <dungeon>` to start adding.")
        return

    dungeon_list = []
    
    for dungeon, bosses in bosses_data.items():
        boss_entries = "\n".join(
            f"  🔴 **{boss.capitalize()}** - {format_duration(time)}"
            for boss, time in bosses.items()
        ) if bosses else "  ❌ No bosses added yet!"
        
        dungeon_list.append(f"🏰 **{dungeon.capitalize()}**\n{boss_entries}")

    formatted_list = "\n\n".join(dungeon_list)
    await ctx.send(f"📜 **Dungeons & Bosses:**\n{formatted_list}")

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
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{minutes}m"
