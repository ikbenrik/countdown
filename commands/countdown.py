import json
import os
import discord
import time
from config import GATHERING_CHANNELS, RARITY_COLORS
from discord.ext import commands

ITEMS_FILE = "items.json"

def load_items():
    """Load items from a JSON file."""
    if os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return {key.lower().strip(): value for key, value in data.items()}  
            except json.JSONDecodeError:
                print("❌ ERROR: Could not decode JSON file.")
                return {}
    else:
        print(f"❌ ERROR: {ITEMS_FILE} not found.")
    return {}

# ✅ Load saved items on startup
item_timers = load_items()

async def cd(bot, ctx, *args):
    """Handles tracking events with the new command structure."""
    global item_timers

    if len(args) < 1:
        await ctx.send("❌ **Invalid format!** Use `!cd <item> [rarity/amount] [time]`.")
        return

    item_name = args[0].lower().strip()
    duration = None
    rarity = "r"
    amount = ""

    duration_mapping = {"h": 3600, "m": 60, "s": 1}
    for arg in args[1:]:
        if arg[-1].lower() in duration_mapping and arg[:-1].isdigit():
            duration = int(arg[:-1]) * duration_mapping[arg[-1].lower()]
            continue

        if any(char in "curhel" for char in arg.lower()) and any(char.isdigit() for char in arg):
            rarity_letter = [char for char in arg.lower() if char in "curhel"]
            amount = "".join(filter(str.isdigit, arg))
            rarity = rarity_letter[0] if rarity_letter else "r"
            continue

    rarity_name, color = RARITY_COLORS.get(rarity, ("Rare", "🔵"))

    if duration is None:
        if item_name in item_timers:
            duration = item_timers[item_name]
        else:
            await ctx.send(f"❌ **{item_name.capitalize()}** is not stored! Use `!cd {item_name} <time>` first.")
            return

    countdown_time = int(time.time()) + duration  

    countdown_text = (
        f"{color} **{amount}x {rarity_name} {item_name.capitalize()}** {color}\n"
        f"👤 **Posted by: {ctx.message.author.display_name}**\n"
        f"⏳ **Next spawn at** <t:{countdown_time}:F>\n"
        f"⏳ **Countdown:** <t:{countdown_time}:R>"
    )

    countdown_message = await ctx.send(countdown_text)

    await countdown_message.add_reaction("✅")
    await countdown_message.add_reaction("🗑️")

    for emoji in GATHERING_CHANNELS.keys():
        await countdown_message.add_reaction(emoji)

    bot.messages_to_delete[countdown_message.id] = (
        countdown_message, duration, item_name.capitalize(), rarity_name, color, amount, ctx.channel.id, ctx.author.display_name
    )
