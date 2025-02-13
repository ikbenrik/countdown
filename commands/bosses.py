import json
import os
import logging
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

async def add_boss(ctx, dungeon: str, boss_name: str = None, time: str = None):
    """Adds a new dungeon or boss inside a dungeon."""
    dungeon = dungeon.lower().strip()
    
    if boss_name:  # ✅ Adding a boss
        boss_name = boss_name.lower().strip()
        
        if not time:
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
                    boss_data[dungeon][boss_name] = time
                    save_bosses(boss_data)
                    await ctx.send(f"✅ **Updated:** `{boss_name.capitalize()}` now spawns in `{time}`.")
                else:
                    await ctx.send("❌ **No changes made.** Boss time remains the same.")

            except TimeoutError:
                await ctx.send("⌛ **No response received.** Boss time remains unchanged.")

        else:
            boss_data[dungeon][boss_name] = time
            save_bosses(boss_data)
            await ctx.send(f"✅ **Added:** `{boss_name.capitalize()}` to `{dungeon.capitalize()}` with a spawn time of `{time}`.")

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
