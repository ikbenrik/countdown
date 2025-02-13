import discord
import time
import logging
import json
import os
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

# ✅ Initialize bosses storage
boss_timers = load_bosses()

# ✅ Convert time format (h, m, s) to seconds
def parse_duration(duration_str):
    duration_mapping = {"h": 3600, "m": 60, "s": 1}
    total_seconds = 0

    try:
        for part in duration_str.split():
            unit = part[-1].lower()
            if unit in duration_mapping and part[:-1].isdigit():
                total_seconds += int(part[:-1]) * duration_mapping[unit]
            else:
                return None  # ❌ Invalid format
        return total_seconds
    except ValueError:
        return None  # ❌ Invalid format

# ✅ Command to add dungeons and bosses
async def add_boss(ctx, dungeon: str, boss: str, time_str: str):
    """Adds a boss to a dungeon with a specific timer."""
    dungeon = dungeon.lower().strip()  # ✅ Normalize dungeon name
    boss = boss.lower().strip()  # ✅ Normalize boss name

    bosses_data = load_bosses()  # ✅ Load latest bosses

    if dungeon not in bosses_data:
        await ctx.send(f"❌ **Dungeon {dungeon.capitalize()} does not exist!** Use `!b add {dungeon}` first.")
        return

    # ✅ Convert time to seconds
    duration = parse_duration(time_str)
    if duration is None:
        await ctx.send("❌ **Invalid time format!** Use `h/m/s` (e.g., `1h 30m`, `3000s`).")
        return

    # ✅ If boss exists, ask for overwrite confirmation
    if boss in bosses_data[dungeon]:
        confirmation = await ctx.send(f"⚠️ **{boss.capitalize()} already exists!** React 👍 to overwrite, 👎 to cancel.")
        await confirmation.add_reaction("👍")
        await confirmation.add_reaction("👎")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["👍", "👎"]

        try:
            reaction, _ = await ctx.bot.wait_for("reaction_add", timeout=30.0, check=check)
            if str(reaction.emoji) == "👎":
                await ctx.send(f"❌ **Boss {boss.capitalize()} update cancelled.**")
                return
        except TimeoutError:
            await ctx.send("⌛ **Boss update cancelled (no response).**")
            return

    # ✅ Store the new boss time
    bosses_data[dungeon][boss] = duration
    save_bosses(bosses_data)

    await ctx.send(f"✅ **Added boss:** {boss.capitalize()} in {dungeon.capitalize()} - `{time_str}`")


# ✅ Command to add a dungeon
async def add_dungeon(ctx, dungeon: str):
    """Adds a dungeon to the boss tracking system."""
    dungeon = dungeon.lower().strip()  # ✅ Normalize name
    bosses_data = load_bosses()  # ✅ Load latest bosses

    if dungeon in bosses_data:
        await ctx.send(f"⚠️ **{dungeon.capitalize()}** already exists!")
    else:
        bosses_data[dungeon] = {}  # ✅ Add new dungeon
        save_bosses(bosses_data)
        await ctx.send(f"✅ **Added dungeon:** {dungeon.capitalize()}")


# ✅ Command to retrieve bosses from a dungeon
async def get_bosses(ctx, dungeon: str):
    """Retrieves all bosses from a dungeon."""
    dungeon = dungeon.lower().strip()  # ✅ Normalize case
    bosses_data = load_bosses()  # ✅ Load latest data

    if dungeon not in bosses_data:
        error_message = await ctx.send(f"❌ **{dungeon.capitalize()}** is not a valid dungeon! Use `!b add <dungeon>` first.")
        await error_message.add_reaction("🗑️")  # ✅ Add delete reaction
        return

    # ✅ Generate events for all bosses in the dungeon
    for boss_name, boss_time in bosses_data[dungeon].items():
        countdown_time = int(time.time()) + boss_time  # ✅ Calculate spawn time

        # ✅ Format the boss event
        boss_text = (
            f"🔴 **{boss_name.capitalize()}** 🔴\n"
            f"👤 **Posted by: {ctx.author.display_name}**\n"
            f"⏳ **Next spawn at** <t:{countdown_time}:F>\n"
            f"⏳ **Countdown:** <t:{countdown_time}:R>\n"
            f"⏳ **Interval:** {boss_time // 60}m"
        )

        message = await ctx.send(boss_text)

        # ✅ Add reactions for refresh and delete
        await message.add_reaction("✅")  # Reset boss event
        await message.add_reaction("🗑️")  # Delete boss event

    try:
        await ctx.message.delete()  # ✅ Delete user command
    except discord.NotFound:
        logging.warning("⚠️ Command message was already deleted.")
    except discord.Forbidden:
        logging.warning("🚫 Bot does not have permission to delete messages in this channel!")
