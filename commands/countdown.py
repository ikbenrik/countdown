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
    
    item_name = args[0].lower().strip()
    duration = None
    rarity = None
    amount = 1
    negative_offset = 0
    duration_mapping = {"h": 3600, "m": 60, "s": 1}

    # ✅ Parse Arguments
    for arg in args[1:]:
        arg = arg.lower()

        if arg[-1] in duration_mapping and arg[:-1].isdigit():
            if duration is None:
                duration = int(arg[:-1]) * duration_mapping[arg[-1]]
            else:
                logging.warning(f"⚠️ Ignored extra duration: {arg}")
            continue

        if any(c in "curhel" for c in arg) and any(c.isdigit() for c in arg):
            rarity_letter = next(c for c in arg if c in "curhel")
            amount_digits = "".join(filter(str.isdigit, arg))
            rarity = rarity_letter
            amount = int(amount_digits) if amount_digits else 1
            continue

        if arg in "curhel":
            rarity = arg
            continue

        if arg.isdigit():
            amount = int(arg)
            continue

        if arg.startswith("-") and arg[1:].isdigit():
            negative_offset = int(arg[1:]) * 60
            continue

    # ✅ Load stored items before checking
    item_timers = load_items()

    # ✅ If no duration is provided, use stored duration
    if duration is None:
        if item_name in item_timers:
            duration = item_timers[item_name]
        else:
            error_message = await ctx.send(f"❌ **{item_name.capitalize()}** is not stored! Use `!cd {item_name} <time>` first.")
            await error_message.add_reaction("🗑️")  # ✅ Add trash bin reaction

            try:
                await ctx.message.delete()
            except discord.NotFound:
                logging.warning("⚠️ Command message was already deleted.")
            except discord.Forbidden:
                logging.warning("🚫 Bot does not have permission to delete messages!")

            return  # ✅ Stop execution if item is not found

    original_duration = duration  # ✅ Store original full duration for resets
    countdown_time = int(time.time()) + max(0, duration - negative_offset)  # ✅ Adjust time

    image_url = None
    file = None

    # ✅ If the user uploaded an image, save the actual file
    if ctx.message.attachments:
        file = await ctx.message.attachments[0].to_file()
        image_url = ctx.message.attachments[0].url  # ✅ Keep URL as backup

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
    
    embed = None
    if image_url:
        embed = discord.Embed()
        embed.set_image(url=image_url)  # ✅ Use embed to store the image properly

    message = await ctx.send(countdown_text, embed=embed)

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
        message, original_duration, duration - negative_offset, negative_offset,
        item_name.capitalize(), rarity_name, color, amount, ctx.channel.id, ctx.author.display_name,
        message.attachments[0].url if message.attachments else None  # ✅ Store actual image URL
    )


    # ✅ Delete the user command message (if exists)
    try:
        await ctx.message.delete()
    except discord.NotFound:
        logging.warning("⚠️ Command message was already deleted.")
    except discord.Forbidden:
        logging.warning("🚫 Bot does not have permission to delete messages in this channel!")
