import re
import time
import discord
from config import GATHERING_CHANNELS
from utils.helpers import load_items

async def handle_reaction(bot, payload):
    """Handles reactions for sharing, claiming, resetting, and deleting timers."""
    if payload.user_id == bot.user.id:
        return  

    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    user = guild.get_member(payload.user_id)

    message = await channel.fetch_message(payload.message_id)
    message_id = payload.message_id
    reaction_emoji = str(payload.emoji)

    if message_id in bot.messages_to_delete:
        message_data = bot.messages_to_delete[message_id]
        message, duration, item_name, rarity_name, color, amount, channel_id, creator_name = message_data

        if reaction_emoji == "✅":
            """🔄 Reset event"""
            new_time = int(time.time()) + duration
            new_message = await channel.send(
                f"{color} **{amount}x {rarity_name} {item_name}** {color}\n"
                f"👤 **Reset by: {user.display_name}**\n"
                f"⏳ **Next spawn at** <t:{new_time}:F>\n"
                f"⏳ **Countdown:** <t:{new_time}:R>\n"
                f"⏳ **Interval: {duration // 3600}h**"
            )

            await new_message.add_reaction("✅")
            await new_message.add_reaction("🗑️")

            bot.messages_to_delete[new_message.id] = (new_message, duration, item_name, rarity_name, color, amount, channel_id, creator_name)
            await message.delete()

        elif reaction_emoji == "🗑️":
            """🗑️ Delete event"""
            await message.delete()
            del bot.messages_to_delete[message_id]

