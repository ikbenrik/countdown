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
                bosses_data[dungeon][boss_name] = duration  # ✅ Store duration in **seconds** (Fix)
                save_bosses(bosses_data)
                await ctx.send(f"✅ **Updated `{boss_name.capitalize()}` timer to {format_duration(duration)}!**")
            else:
                await ctx.send("❌ **Boss timer update cancelled.**")
            return
        except TimeoutError:
            await ctx.send("⌛ **Boss overwrite request timed out.**")
            return

    # ✅ Store the boss inside the dungeon (Duration in **seconds**)
    bosses_data[dungeon][boss_name] = duration
    save_bosses(bosses_data)

    await ctx.send(f"🔴 **Added Boss:** `{boss_name.capitalize()}` in `{dungeon.capitalize()}` with a timer of `{format_duration(duration)}`.")

async def get_bosses(ctx, dungeon: str):
    """Creates event messages for all bosses in a dungeon."""
    dungeon = dungeon.lower().strip()

    if dungeon not in bosses_data:
        error_msg = await ctx.send(f"❌ **Dungeon `{dungeon.capitalize()}` not found!** Use `!b add {dungeon}` to create it.")
        await error_msg.add_reaction("🗑️")  # ✅ Add trash bin reaction
        return

    if not bosses_data[dungeon]:
        error_msg = await ctx.send(f"🏰 **{dungeon.capitalize()}** has no bosses added yet!")
        await error_msg.add_reaction("🗑️")
        return

    # ✅ Generate an event for each boss
    for boss, duration in bosses_data[dungeon].items():
        countdown_time = int(time.time()) + duration

        countdown_text = (
            f"🔴 **{boss.capitalize()}** 🔴\n"
            f"👤 **Posted by: {ctx.author.display_name}**\n"
            f"⏳ **Next spawn at** <t:{countdown_time}:F>\n"
            f"⏳ **Countdown:** <t:{countdown_time}:R>\n"
            f"⏳ **Interval:** {format_duration(duration)}"
        )

        message = await ctx.send(countdown_text)

        # ✅ Add event reactions
        await message.add_reaction("✅")  # Reset
        await message.add_reaction("🗑️")  # Delete
        await message.add_reaction("🔔")  # Ping notification

    # ✅ Delete the command message
    try:
        await ctx.message.delete()
    except discord.NotFound:
        logging.warning("⚠️ Command message was already deleted.")

async def list_all_bosses(ctx):
    """Displays all dungeons and their bosses with timers."""
    bosses_data = load_bosses()  # ✅ Reload latest data

    if not bosses_data:
        error_msg = await ctx.send("❌ **No dungeons or bosses found!** Use `!b add <dungeon>` to start adding.")
       
