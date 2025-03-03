import discord
import config
import time
import logging
from events.ping_manager import track_ping_reaction, remove_ping_reaction, delete_pings_for_event  # ✅ Import ping management

async def handle_reaction(bot, payload):
    logging.debug("🚨 DEBUG: handle_reaction() function was triggered!")  

    if payload.user_id == bot.user.id:
        return  # ✅ Ignore bot reactions

    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    user = guild.get_member(payload.user_id)

    if not user or user.bot:
        return  

    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.NotFound:
        return  

    reaction_emoji = str(payload.emoji)

    # ✅ Handle Bell reaction (Ping system)
    if reaction_emoji == "🔔":
        if payload.event_type == "REACTION_REMOVE":
            await remove_ping_reaction(bot, payload)
            logging.info(f"❌ {user.display_name} removed from pings for event {message.id}")
        else:
            await track_ping_reaction(bot, payload)
        return  

    # ✅ Auto-delete event messages when clicking 🗑️
    if reaction_emoji == "🗑️" and message.author == bot.user:
        await delete_pings_for_event(bot, message.id)  # ✅ Remove all associated pings
        logging.info(f"🗑️ Pings cleared for event {message.id} due to delete reaction.")
        await message.delete()
        bot.messages_to_delete.pop(message.id, None)
        return  

    # ✅ Ensure the event exists in tracking
    if message.id not in bot.messages_to_delete:
        return

    message_data = bot.messages_to_delete[message.id]
    message, original_duration, remaining_duration, negative_adjustment, item_name, rarity_name, color, amount, channel_id, creator_name, image_url = message_data

    current_time = int(time.time())

    # ✅ Calculate the actual remaining time based on when the event was created
    elapsed_time = current_time - int(message.created_at.timestamp())
    actual_remaining_time = max(0, (int(message.created_at.timestamp()) + remaining_duration) - current_time)

    # ✅ Correct new spawn time calculation
    if reaction_emoji == "✅":
        new_spawn_time = current_time + original_duration  # ✅ Full reset
        actual_remaining_time = original_duration
    else:
        new_spawn_time = current_time + actual_remaining_time  # ✅ Keep correct time when sharing or claiming

    # ✅ Universal Event Format
    def generate_event_text(actor: str, action: str) -> str:
        return (
            f"{color} **{amount}x {rarity_name} {item_name}** {color}\n"
            f"👤 **{action} by: {actor}**\n"
            f"⏳ **Next spawn at** <t:{new_spawn_time}:F>\n"
            f"⏳ **Countdown:** <t:{new_spawn_time}:R>\n"
            f"⏳ **Interval: {original_duration//60}m**"
        )

    reset_reactions = []  

    # ✅ Reset Event (Restore full event duration)
    if reaction_emoji == "✅":
        await delete_pings_for_event(bot, message.id)
        logging.info(f"🗑️ Pings cleared for event {message.id} due to reset reaction.")

        event_text = generate_event_text(user.display_name, "Reset")
        channel = channel  

        if channel.name in config.GATHERING_CHANNELS.values():
            reset_reactions = ["📥", "🔔"]
        else:
            reset_reactions = list(config.GATHERING_CHANNELS.keys()) + ["🔔"]

    # ✅ Share Event (Keep Correct Remaining Time)
    elif reaction_emoji in config.GATHERING_CHANNELS:
        new_channel_name = config.GATHERING_CHANNELS[reaction_emoji]
        target_channel = discord.utils.get(guild.channels, name=new_channel_name)

        if target_channel:
            event_text = generate_event_text(user.display_name, "Shared")
            channel = target_channel  
            reset_reactions = ["📥"]

    # ✅ Claim Event (Keep Correct Remaining Time)
    elif reaction_emoji == "📥":
        user_channel_name = user.display_name.lower().replace(" ", "-")
        personal_category = next((cat for cat in guild.categories if cat.name.lower() == "personal intel"), None)

        if not personal_category:
            return

        user_channel = discord.utils.get(guild.text_channels, name=user_channel_name, category=personal_category)

        if not user_channel:
            user_channel = await guild.create_text_channel(name=user_channel_name, category=personal_category)

        event_text = generate_event_text(user.display_name, "Claimed")
        channel = user_channel
        reset_reactions = list(config.GATHERING_CHANNELS.keys())

    # ✅ Send the updated event message
    file = None
    if message.attachments:
        file = await message.attachments[0].to_file()

    if file:
        new_message = await channel.send(event_text, file=file)
    else:
        new_message = await channel.send(event_text)

    # ✅ Add reactions
    await new_message.add_reaction("✅")
    await new_message.add_reaction("🗑️")
    await new_message.add_reaction("🔔")
    
    for emoji in reset_reactions:
        await new_message.add_reaction(emoji)

    # ✅ Store event with correct remaining time
    bot.messages_to_delete[new_message.id] = (
        new_message, original_duration, actual_remaining_time, negative_adjustment,
        item_name.capitalize(), rarity_name, color, amount, channel.id, creator_name,
        file
    )

    await message.delete()  # ✅ Remove old message
