import discord
import config
import time

async def handle_reaction(bot, payload):
    print("🔎 DEBUG: handle_reaction() was triggered!")  # Add this line
    """Handles reactions: reset, delete, share, and claim."""
    if payload.user_id == bot.user.id:
        return  

    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    user = guild.get_member(payload.user_id)

    if not user or user.bot:
        return  

    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.NotFound:
        print(f"❌ ERROR: Message {payload.message_id} not found. Probably deleted.")
        return  

    reaction_emoji = str(payload.emoji)
    print(f"🔍 Reaction detected: {reaction_emoji} by {user.display_name}")

    # ✅ Check if the message exists in bot tracking
    if message.id in bot.messages_to_delete:
        message_data = bot.messages_to_delete[message.id]
        message, original_duration, item_name, rarity_name, color, amount, channel_id, creator_name = message_data

        current_time = int(time.time())
        event_creation_time = int(message.created_at.timestamp())
        remaining_time = max(0, original_duration - (current_time - event_creation_time))

        # ✅ Debugging prints to verify time calculations
        print(f"DEBUG: Current Time: {current_time}")
        print(f"DEBUG: Event Created At: {event_creation_time}")
        print(f"DEBUG: Remaining Time: {remaining_time}")
        print(f"DEBUG: Original Duration: {original_duration}")

        # ✅ Reset Event
        if reaction_emoji == "✅":
            print(f"🔄 Resetting event: {item_name}")
            new_end_time = current_time + original_duration
            reset_text = (
                f"{color} **{amount}x {rarity_name} {item_name}** {color}\n"
                f"👤 **Reset by: {user.display_name}**\n"
                f"⏳ **Next spawn at** <t:{new_end_time}:F>\n"
                f"⏳ **Countdown:** <t:{new_end_time}:R>\n"
                f"⏳ **Interval: {original_duration//60}m**"
            )

            new_message = await channel.send(reset_text)
            await new_message.add_reaction("✅")
            await new_message.add_reaction("🗑️")

            # ✅ Check if it's in a shared channel or not
            if channel.name in config.GATHERING_CHANNELS.values():
                await new_message.add_reaction("📥")  # Claim reaction for shared channels
            else:
                for emoji in config.GATHERING_CHANNELS.keys():
                    await new_message.add_reaction(emoji)  # Share reactions

            bot.messages_to_delete[new_message.id] = (
                new_message, original_duration, item_name, rarity_name, color, amount, channel_id, creator_name
            )
            await message.delete()

        # ✅ Delete Event
        elif reaction_emoji == "🗑️":
            print(f"🗑️ Deleting event: {item_name}")
            await message.delete()
            del bot.messages_to_delete[message.id]

        elif reaction_emoji in config.GATHERING_CHANNELS:
            new_channel_name = config.GATHERING_CHANNELS[reaction_emoji]
            target_channel = discord.utils.get(guild.channels, name=new_channel_name)

    if target_channel:
        print(f"📤 Sharing event: {item_name} to {new_channel_name}")

        # ✅ Calculate remaining time correctly
        new_end_time = current_time + remaining_time  # ✅ Keeps remaining time instead of resetting

        shared_text = (
            f"{color} **{amount}x {rarity_name} {item_name}** {color}\n"
            f"👤 **Shared by: {user.display_name}**\n"
            f"⏳ **Next spawn at** <t:{new_end_time}:F>\n"
            f"⏳ **Countdown:** <t:{new_end_time}:R>\n"
            f"⏳ **Interval: {original_duration//60}m**"  # Still show full interval
        )

        new_message = await target_channel.send(shared_text)
        await new_message.add_reaction("✅")  # Reset
        await new_message.add_reaction("🗑️")  # Delete
        await new_message.add_reaction("📥")  # Claim reaction for shared channels

        # ✅ Track new message with the **remaining time**
        bot.messages_to_delete[new_message.id] = (
            new_message, remaining_time, item_name, rarity_name, color, amount, target_channel.id, creator_name
        )


        # ✅ Delete the original message after sharing
        await message.delete()

