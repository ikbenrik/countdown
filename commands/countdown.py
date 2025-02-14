import time
import discord
import config
import logging
import aiohttp
import io
from utils.helpers import load_items

async def repost_image(ctx, attachment):
    """Downloads and re-uploads an image properly to prevent embed issues."""
    async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as resp:
            if resp.status == 200:
                image_data = await resp.read()
                file = discord.File(io.BytesIO(image_data), filename=attachment.filename)
                return file
    return None

async def cd(bot, ctx, *args):
    """Handles event creation and tracking with optional images and negative time adjustments."""

    # ✅ If no arguments, send error message and delete user command
    if len(args) < 1:
        error_message = await ctx.send("❌ **Invalid format!** Use `!cd <item> [rarity/amount] [time] [-X minutes]`.")
        await error_message.add_reaction("🗑️")  # ✅ Add trash bin reaction
        try:
            await ctx.message.delete()  # ✅ Delete user command
        except discord.NotFound:
            logging.warning("⚠️ Command message was already deleted.")
        return

    item_name = args[0].lower().strip()
    duration = None
    rarity = None  # ✅ Default: No rarity
    amount = 1  # ✅ Default: 1 (if no amount is provided)
    negative_offset = 0  # Default: No negative offset
    duration_mapping = {"h": 3600, "m": 60, "s": 1}

    # ✅ Process arguments
    for arg in args[1:]:
        if arg[-1].lower() in duration_mapping and arg[:-1].isdigit():
            duration = int(arg[:-1]) * duration_mapping[arg[-1].lower()]
            continue

        # ✅ Detect rarity + amount (e.g., "5r" or "r5")
        if any(char in "curhel" for char in arg.lower()) and any(char.isdigit() for char in arg):
            rarity_letter = [char for char in arg.lower() if char in "curhel"][0]
            amount_digits = "".join(filter(str.isdigit, arg))
            rarity = rarity_letter  # ✅ Assign rarity
            amount = int(amount_digits) if amount_digits else 1  # ✅ Assign amount (default: 1)
            continue

        # ✅ Detect rarity when only a rarity letter is given (e.g., "!cd lion r")
        if arg.lower() in "curhel":
            rarity = arg.lower()
            continue

        # ✅ Detect amount when only a number is given (e.g., "!cd lion 5")
        if arg.isdigit():
            amount = int(arg)
            continue

        # ✅ Detect negative time offset (-X minutes)
        if arg.startswith("-") and arg[1:].isdigit():
            negative_offset = int(arg[1:]) * 60  # Convert minutes to seconds
            continue

    # ✅ Load stored items before checking
    item_timers = load_items()

    # ✅ If no duration provided, try using stored duration
    if duration is None:
        if item_name in item_timers:
            duration = item_timers[item_name]
        else:
            error_message = await ctx.send(f"❌ **{item_name.capitalize()}** is not stored! Use `!cd {item_name} <time>` first.")
            try:
                await error_message.add_reaction("🗑️")  # ✅ Add trash bin reaction
            except discord.Forbidden:
                logging.warning("🚫 Bot does not have permission to add reactions to messages!")
            
            # ✅ Delete user command message
            try:
                await ctx.message.delete()
            except discord.NotFound:
                logging.warning("⚠️ Command message was already deleted.")
            except discord.Forbidden:
                logging.warning("🚫 Bot does not have permission to delete messages!")

            return  # ✅ Stop execution if item is not found

    original_duration = duration  # ✅ Store original full duration for resets
    countdown_time = int(time.time()) + max(0, duration - negative_offset)  # ✅ Adjust time

    # ✅ Capture image attachment if provided
    image_url = None
    if ctx.message.attachments:
        image_url = ctx.message.attachments[0].url  # Take the first attached image

    # ✅ Determine rarity color dynamically
    if rarity:
        rarity_name, color = config.RARITY_COLORS.get(rarity, ("Rare", "🔵"))  # ✅ Use correct rarity letter
        rarity_display = f"{rarity_name} "
        amount_display = f"{amount}x " if amount > 1 else ""
    else:
        rarity_name, color = "", "⚪"  # ✅ Default: No rarity name, white dots
        rarity_display = ""
        amount_display = f"{amount}x " if amount > 1 else ""  # ✅ Still show amount if > 1

    # ✅ Build countdown message
    countdown_text = (
        f"{color} **{amount_display}{rarity_display}{item_name.capitalize()}** {color}\n"  # ✅ Displays "5x Rare Lion"
        f"👤 **Posted by: {ctx.author.display_name}**\n"
        f"⏳ **Next spawn at** <t:{countdown_time}:F>\n"
        f"⏳ **Countdown:** <t:{countdown_time}:R>\n"
        f"⏳ **Interval:** {original_duration // 3600}h"
    )

    if original_duration % 3600 != 0:
        countdown_text += f" {original_duration % 3600 // 60}m"

    # ✅ Send message with image (if exists)
    embed = discord.Embed()
    if image_url:
        embed.set_image(url=image_url)
    
    message = await ctx.send(countdown_text, embed=embed if image_url else None)

    # ✅ Always add reset and delete reactions
    await message.add_reaction("✅")  # Reset event
    await message.add_reaction("🗑️")  # Delete event
    await message.add_reaction("🔔")  # ✅ Add ping reaction

    # ✅ Check if the event is in a shared gathering channel
    if ctx.channel.name in config.GATHERING_CHANNELS.values():
        await message.add_reaction("📥")  # Add claim reaction in shared channels
    else:
        for emoji in config.GATHERING_CHANNELS.keys():
            await message.add_reaction(emoji)  # ✅ Add sharing reactions (⛏️, 🌲, 🌿)

    # ✅ Store message details, including the original duration and image URL
    bot.messages_to_delete[message.id] = (
        message, original_duration, duration - negative_offset, negative_offset,  # ✅ Store the negative offset
        item_name.capitalize(), rarity_name, color, amount, ctx.channel.id, ctx.author.display_name, image_url
    )

    # ✅ Delete the user command message (if exists)
    try:
        await ctx.message.delete()
    except discord.NotFound:
        logging.warning("⚠️ Command message was already deleted.")
    except discord.Forbidden:
        logging.warning("🚫 Bot does not have permission to delete messages in this channel!")
