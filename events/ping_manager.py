import asyncio
import time
import logging
import discord

# ✅ Dictionary to store user IDs who reacted to the 🔔 for each event
event_pings = {}

async def track_ping_reaction(bot, payload):
    """Tracks users reacting with 🔔 to be notified when the event is about to expire."""
    logging.debug(f"🔔 Tracking ping reaction: {payload.emoji.name} by {payload.user_id}")

    if payload.emoji.name != "🔔":
        return

    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    message_id = payload.message_id
    user = guild.get_member(payload.user_id)

    if not user or user.bot:
        return  # Ignore bot reactions

    if message_id not in event_pings:
        event_pings[message_id] = set()

    event_pings[message_id].add(user.id)
    logging.info(f"✅ {user.display_name} will be pinged for event {message_id}")

async def remove_ping_reaction(bot, payload):
    """Removes users from the ping list when they remove their 🔔 reaction."""
    logging.debug(f"🔕 Removing ping reaction: {payload.emoji.name} by {payload.user_id}")

    if payload.emoji.name != "🔔":
        return

    message_id = payload.message_id

    if message_id in event_pings and payload.user_id in event_pings[message_id]:
        event_pings[message_id].remove(payload.user_id)
        logging.info(f"❌ {payload.user_id} removed from pings for event {message_id}")

        if not event_pings[message_id]:  # ✅ If no users remain, remove event
            del event_pings[message_id]

@bot.event
async def on_raw_reaction_remove(payload):
    """Detect when a user removes a reaction."""
    await remove_ping_reaction(bot, payload)
