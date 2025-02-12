import time
import discord
import config
from utils.helpers import load_items

# ✅ Load saved items
item_timers = load_items()

async def cd(bot, ctx, *args):
    """Handles event creation and tracking with optional negative time."""
    if len(args) < 1:
        await ctx.send("❌ **Invalid format!** Use `!cd <item> [rarity/amount] [time] [-X minutes]`.")
        return

    item_name = args[0].lower().strip()
    duration = None
    rarity = "r"
    amount = ""
    negative_offset = 0  # Default: No negative offset

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

        # ✅ Detect negative time offset (-X minutes)
        if arg.startswith("-") and arg[1:].isdigit():
            negative_offset = int(arg[1:]) * 60  # Convert minutes to seconds
            continue

    rarity_name, color = config.RARITY_COLORS.get(rarity, ("Rare", "🔵"))

    # ✅ If no duration was provided, check item storage
    if duration is None:
        if item_name in item_timers:
            duration = item_timers[item_name]
        else:
            await ctx.send(f"❌ **{item_name.capitalize()}** is not stored! Use `!cd {item_name} <time>` first.")
            return

    original_duration = duration  # ✅ Store original full duration for resets
    countdown_time = int(time.time()) + max(0, duration - negative_offset)  # ✅ Adjust time

    countdown_text = (
        f"{color} **{amount}x {rarity_name} {item_name.capitalize()}** {color}\n"
        f"👤 **Posted by: {ctx.author.display_name}**\n"
        f"⏳ **Next spawn at** <t:{countdown_time}:F>\n"
        f"⏳ **Countdown:** <t:{countdown_time}:R>\n"
        f"⏳ **Interval: {original_duration//60}m**"
    )

    message = await ctx.send(countdown_text)

    # ✅ Always add reset and delete reactions
    await message.add_reaction("✅")  # Reset event
    await message.add_reaction("🗑️")  # Delete event

    # ✅ Check if the event is in a shared gathering channel
    if ctx.channel.name in config.GATHERING_CHANNELS.values():
        await message.add_reaction("📥")  # Add claim reaction in shared channels
    else:
        for emoji in config.GATHERING_CHANNELS.keys():
            await message.add_reaction(emoji)  # ✅ Add sharing reactions (⛏️, 🌲, 🌿)

    # ✅ Store message details, including the original duration
    bot.messages_to_delete[message.id] = (
        message, original_duration, duration - negative_offset,  # ✅ Store remaining time correctly
        item_name.capitalize(), rarity_name, color, amount, ctx.channel.id, ctx.author.display_name
)
