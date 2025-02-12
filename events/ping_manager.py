import asyncio
import time
import logging
import discord

# ✅ Dictionary to store user IDs who reacted to the 🔔 for each event
event_pings = {}

async def track_ping_reaction(bot, payload):
    """Tracks users reacting with 🔔 to be notified when the event is about to expire."""
    logging.debug(f"🔔 Tracking ping reaction: {payload.emoji.name} by {payload.user_id}")

    if payload.emoji.name != "🔔":  # Only track the bell reaction
        return

    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    message_id = payload.message_id
    user = guild.get_member(payload.user_id)

    if not user or user.bot:
        return  # Ignore bot reactions

    # ✅ Add user to the ping list for this event
    if message_id not in event_pings:
        event_pings[message_id] = set()

    event_pings[message_id].add(user.id)
    logging.info(f"✅ {user.display_name} will be pinged for event {message_id}")

async def remove_ping_reaction(bot, payload):
    """Removes users from the ping list when they remove their 🔔 reaction."""
    logging.debug(f"🔕 Removing ping reaction: {payload.emoji.name} by {payload.user_id}")

    if payload.emoji.name != "🔔":  # Only remove if it's the bell reaction
        return

    message_id = payload.message_id

    # ✅ Remove user from the ping list
    if message_id in event_pings and payload.user_id in event_pings[message_id]:
        event_pings[message_id].remove(payload.user_id)
        logging.info(f"❌ {payload.user_id} removed from pings for event {message_id}")

        # ✅ If no users remain, remove the event entry
        if not event_pings[message_id]:
            del event_pings[message_id]

async def delete_pings_for_event(message_id):
    """Removes all pings associated with a deleted or reset event."""
    if message_id in event_pings:
        del event_pings[message_id]
        logging.info(f"🗑️ All pings removed for event {message_id} (event deleted/reset)")

async def schedule_pings(bot):
    """Background task that checks for events reaching 15 minutes remaining and pings users."""
    while True:
        current_time = int(time.time())
        to_remove = []

        for message_id, users in list(event_pings.items()):  # ✅ Use list() to prevent runtime issues
            if message_id in bot.messages_to_delete:
                event_data = bot.messages_to_delete[message_id]
                message, original_duration, stored_remaining_time, negative_adjustment, item_name, rarity, color, amount, channel_id, creator_name, image_url = event_data
                
                event_creation_time = int(message.created_at.timestamp())  # ✅ Get event creation time
                actual_time_left = max(0, (event_creation_time + stored_remaining_time) - current_time)  # ✅ Dynamically calculate remaining time

                # ✅ Debugging logs
                logging.debug(f"🔎 Checking pings: {message_id} | Time Left: {actual_time_left}s")

                if 900 <= actual_time_left < 960:  # ✅ Ping when 15 minutes left
                    logging.info(f"🔔 Sending ping for event {message_id}")

                    channel = bot.get_channel(channel_id)
                    if channel:
                        mentions = " ".join([f"<@{user_id}>" for user_id in users])
                        event_link = f"[Click here]({message.jump_url})"  # ✅ Include event link in the ping

                        try:
                            await channel.send(f"🔔 **Reminder!** {item_name} event ends in **15 minutes!** {mentions} {event_link}")
                        except discord.Forbidden:
                            logging.error(f"🚫 Bot lacks permission to send messages in {channel.name}!")
                        except discord.HTTPException as e:
                            logging.error(f"❌ Failed to send ping: {e}")

                    to_remove.append(message_id)  # ✅ Remove event after ping is sent

        # ✅ Remove processed events
        for msg_id in to_remove:
            event_pings.pop(msg_id, None)

        await asyncio.sleep(30)  # ✅ Check every 30 seconds
