import discord
import re
import config

async def handle_reaction(bot, payload):
    """Handles all reactions: reset, delete, share, claim."""
    if payload.user_id == bot.user.id:
        return  

    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    user = guild.get_member(payload.user_id)

    if not user or user.bot:
        return  

    message = await channel.fetch_message(payload.message_id)
    reaction_emoji = str(payload.emoji)

    print(f"🔍 Reaction detected: {reaction_emoji} by {user.display_name}")

    if message.id in bot.messages_to_delete:
        message_data = bot.messages_to_delete[message.id]
        message, duration, item_name, rarity_name, color, amount, channel_id, creator_name = message_data

        if reaction_emoji == "✅":
            print(f"🔄 Resetting event: {item_name}")
            new_message = await channel.send(message.content)
            await new_message.add_reaction("✅")
            await new_message.add_reaction("🗑️")

            bot.messages_to_delete[new_message.id] = (
                new_message, duration, item_name, rarity_name, color, amount, channel_id, creator_name
            )
            await message.delete()

        elif reaction_emoji == "🗑️":
            print(f"🗑️ Deleting event: {item_name}")
            await message.delete()
            del bot.messages_to_delete[message.id]

        elif reaction_emoji in config.GATHERING_CHANNELS:
            new_channel = config.GATHERING_CHANNELS[reaction_emoji]
            target_channel = discord.utils.get(guild.channels, name=new_channel)
            if target_channel:
                await target_channel.send(message.content)
                await message.delete()
