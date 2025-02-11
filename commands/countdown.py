import time
import re
import discord
from discord.ext import commands
from config import GATHERING_CHANNELS, RARITY_COLORS
from utils.helpers import load_items

item_timers = load_items()

async def cd(ctx, *args):
    """Handles tracking events with the new command structure."""
    if len(args) < 1:
        await ctx.send("❌ **Invalid format!** Use `!cd <item> [rarity/amount] [time] [-X minutes]`.")
        return

    item_name = args[0].lower().strip()
    duration = None
    rarity = "r"
    amount = ""
    past_offset = 0

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

        if arg.startswith("-") and arg[1:].isdigit():
            past_offset = int(arg[1:]) * 60  # Convert minutes to seconds

    rarity_name, color = RARITY_COLORS.get(rarity, ("Rare", "🔵"))

    if duration is None:
        if item_name in item_timers:
            duration = item_timers[item_name]
        else:
            await ctx.send(f"❌ **{item_name.capitalize()}** is not stored! Use `!cd {item_name} <time>` first.")
            return

    countdown_time = int(time.time()) + duration - past_offset

    countdown_text = (
        f"{color} **{amount}x {rarity_name} {item_name.capitalize()}** {color}\n"
        f"👤 **Posted by: {ctx.author.display_name}**\n"
        f"⏳ **Next spawn at** <t:{countdown_time}:F>\n"
        f"⏳ **Countdown:** <t:{countdown_time}:R>\n"
        f"⏳ **Interval: {duration // 3600}h**"
    )

    countdown_message = await ctx.send(countdown_text)

    await countdown_message.add_reaction("✅")
    await countdown_message.add_reaction("🗑️")
    for emoji in GATHERING_CHANNELS.keys():
        await countdown_message.add_reaction(emoji)

    return countdown_message, duration, item_name, rarity_name, color, amount, ctx.channel.id, ctx.author.display_name
