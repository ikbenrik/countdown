import discord

async def handle_reaction(bot, payload):
    """Handles reactions for resetting, deleting, sharing, and claiming events."""
    if not hasattr(bot, "messages_to_delete"):  
        bot.messages_to_delete = {}  # ✅ Prevents crashes

    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)

    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.NotFound:
        print(f"❌ ERROR: Message {payload.message_id} not found. Likely deleted.")
        return  
    except discord.Forbidden:
        print(f"❌ ERROR: Bot lacks permission to fetch message {payload.message_id}.")
        return
    except discord.HTTPException:
        print(f"❌ ERROR: Failed to fetch message {payload.message_id}.")
        return

    user = guild.get_member(payload.user_id)
    if not user or user.bot:  # Ignore bot reactions
        return

    reaction_emoji = str(payload.emoji)

    print(f"🔍 Reaction detected: {reaction_emoji} by {user.display_name}")

    # ✅ Ensure the message is being tracked
    if payload.message_id in bot.messages_to_delete:
        message_data = bot.messages_to_delete[payload.message_id]

        if not message_data:
            print(f"⚠️ Warning: Message {payload.message_id} already processed. Skipping.")
            return

        message, duration, item_name, rarity_name, color, amount, channel_id, creator_name, attachments = message_data

        if reaction_emoji == "✅":
            print(f"🔄 Resetting event: {item_name}")

            # ✅ Create a new event message
            new_message = await channel.send(message.content)

            # ✅ Re-add reactions
            await new_message.add_reaction("✅")
            await new_message.add_reaction("🗑️")

            # ✅ Track the new message before deleting old one
            bot.messages_to_delete[new_message.id] = (
                new_message, duration, item_name, rarity_name, color, amount, channel_id, creator_name, attachments
            )

            try:
                await message.delete()
                print(f"✅ Old message {payload.message_id} deleted successfully.")
                del bot.messages_to_delete[payload.message_id]
            except discord.NotFound:
                print(f"⚠️ Warning: Old message {payload.message_id} already deleted.")

        elif reaction_emoji == "🗑️":
            print(f"🗑️ Deleting event: {item_name}")

            if payload.message_id in bot.messages_to_delete:
                del bot.messages_to_delete[payload.message_id]

            try:
                await message.delete()
                print(f"✅ Message {payload.message_id} deleted successfully.")
            except discord.NotFound:
                print(f"⚠️ Warning: Message {payload.message_id} was already deleted.")
