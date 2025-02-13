import json
import os
import logging
import time
import discord

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

boss_data = load_bosses()

async def add_boss(ctx, dungeon: str, boss_name: str = None, time_str: str = None):
    """Adds a new dungeon or boss inside a dungeon."""
    dungeon = dungeon.lower().strip()
    
    if boss_name:  # ✅ Adding a boss
        boss_name = boss_name.lower().strip()
        
        if not time_str:
            error_message = await ctx.send("❌ **Missing time!** Use `!b add <dungeon> <boss> <time>`.")
            await error_message.add_reaction("🗑️")  # ✅ Add trash bin reaction
            return
        
        if dungeon not in boss_data:
            boss_data[dungeon] = {}  # ✅ Create dungeon if it doesn't exist

        # ✅ Check if boss exists & ask to overwrite
        if boss_name in boss_data[dungeon]:
            confirm_message = await ctx.send(
                f"⚠️ **{boss_name.capitalize()}** already exists in `{dungeon.capitalize()}` with time `{boss_data[dungeon][boss_name]}`.\n"
                "Do you want to overwrite it?"
            )
            await confirm_message.add_reaction("👍")
            await confirm_message.add_reaction("👎")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["👍", "👎"]

            try:
                reaction, _ = await ctx.bot.wait_for("reaction_add", timeout=30.0, check=check)

                if str(reaction.emoji) == "👍":
                    boss_data[dungeon][boss_name] = time_str
                    save_bosses(boss_data)
                    await ctx.send(f"✅ **Updated:** `{boss_name.capitalize()}` now spawns in `{time_str}`.")
                else:
                    await ctx.send("❌ **No changes made.** Boss time remains the same.")

            except TimeoutError:
                await ctx.send("⌛ **No response received.** Boss time remains unchanged.")

        else:
            boss_data[dungeon][boss_name] = time_str
            save_bosses(boss_data)
            await ctx.send(f"✅ **Added:** `{boss_name.capitalize()}` to `{dungeon.capitalize()}` with a spawn time of `{time_str}`.")

    else:  # ✅ Adding a dungeon
        if dungeon in boss_data:
            await ctx.send(f"⚠️ **Dungeon `{dungeon.capitalize()}` already exists!**")
        else:
            boss_data[dungeon] = {}
            save_bosses(boss_data)
            await ctx.send(f"✅ **Dungeon `{dungeon.capitalize()}` added!**")

    try:
        await ctx.message.delete()  # ✅ Delete user command
    except discord.NotFound:
        logging.warning("⚠️ Command message was already deleted.")
    except discord.Forbidden:
        logging.warning("🚫 Bot does not have permission to delete messages in this channel!")

async def spawn_boss_event(bot, ctx, dungeon: str, boss_name: str = None):
    """Creates an event message for a boss or all bosses in a dungeon."""
    dungeon = dungeon.lower().strip()
    
    if dungeon not in boss_data:
        error_message = await ctx.send(f"❌ **Dungeon `{dungeon.capitalize()}` not found!** Use `!b add <dungeon>` first.")
        await error_message.add_reaction("🗑️")
        return

    bosses_to_spawn = boss_data[dungeon] if not boss_name else {boss_name.lower().strip(): boss_data[dungeon].get(boss_name.lower().strip())}
    
    if not bosses_to_spawn or None in bosses_to_spawn.values():
        error_message = await ctx.send(f"❌ **Boss `{boss_name.capitalize()}` not found in `{dungeon.capitalize()}`!** Use `!b add <dungeon> <boss> <time>` first.")
        await error_message.add_reaction("🗑️")
        return

    for boss, time_str in bosses_to_spawn.items():
        countdown_time = int(time.time()) + convert_time_to_seconds(time_str)
        
        boss_event_text = (
            f"🔴 **{boss.capitalize()}** 🔴\n"
            f"👤 **Posted by: {ctx.author.display_name}**\n"
            f"⏳ **Next spawn at** <t:{countdown_time}:F>\n"
            f"⏳ **Countdown:** <t:{countdown_time}:R>\n"
            f"⏳ **Interval:** {time_str}"
        )

        message = await ctx.send(boss_event_text)

        # ✅ Always add reset and delete reactions
        await message.add_reaction("✅")
        await message.add_reaction("🗑️")
        await message.add_reaction("🔔")

        bot.messages_to_delete[message.id] = (
            message, countdown_time, time_str, ctx.channel.id, ctx.author.display_name
        )

async def list_dungeons(ctx):
    """Lists all available dungeons and their bosses."""
    if not boss_data:
        await ctx.send("📜 **No dungeons available!** Use `!b add <dungeon>` to create one.")
        return
    
    dungeon_list = "\n".join([f"🏰 **{dungeon.capitalize()}**" for dungeon in boss_data.keys()])
    await ctx.send(f"📜 **Available Dungeons:**\n{dungeon_list}")

async def list_bosses(ctx, dungeon: str):
    """Lists all bosses inside a dungeon."""
    dungeon = dungeon.lower().strip()
    
    if dungeon not in boss_data:
        await ctx.send(f"❌ **Dungeon `{dungeon.capitalize()}` not found!** Use `!b add <dungeon>` first.")
        return

    boss_list = "\n".join([f"🔴 **{boss.capitalize()}** - {time}" for boss, time in boss_data[dungeon].items()])
    await ctx.send(f"📜 **Bosses in `{dungeon.capitalize()}`:**\n{boss_list}")

def convert_time_to_seconds(time_str):
    """Converts a time string (e.g., '2h 30m') into seconds."""
    duration_mapping = {"h": 3600, "m": 60, "s": 1}
    try:
        return sum(int(value[:-1]) * duration_mapping[value[-1]] for value in time_str.split() if value[-1] in duration_mapping and value[:-1].isdigit())
    except ValueError:
        return 0  # Default to 0 seconds if parsing fails
