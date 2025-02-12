import discord
import config
import time
import logging
from events.ping_manager import track_ping_reaction, remove_ping_reaction  # ✅ Import ping management

async def handle_reaction(bot, payload):
    logging.debug("🚨 DEBUG: handle_reaction() function was triggered!")  

    if payload.user_id == bot.user.id:
        print("🚫 Ignoring bot reaction.")
        return  

    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    user = guild.get_member(payload.user_id)

    if not user or user.bot:
        print("🚫 Ignoring bot or missing user.")
        return  

    try:
        message = await channel.fetch_message(payload.message_id)
        print(f"📩 Fetched message {message.id} in #{channel.name}")
    except discord.NotFound:
        print(f"❌ ERROR: Message {payload.message_id} not found. Probably deleted.")
        return  

    reaction_emoji = str(payload.emoji)
    print(f"🔍 Reaction detected: {reaction_emoji} by {user.display_name}")

    # ✅ Handle Bell reaction (Ping system)
    if reaction_emoji == "🔔":
        await track_ping_reaction(bot, payload)

    # ✅ Remove user from pings if they remove 🔔 reaction
    if hasattr(payload, 'event_type') and payload.event_type == "REACTION_REMOVE" and reaction_emoji == "🔔":
        await remove_ping_reaction(bot, payload)

    # ✅ Auto-delete bot messages when clicking 🗑️
    if reaction_emoji == "🗑️" and message.author == bot.user:
        print(f"🗑️ Deleting bot message: {message.id} in #{channel.name}")
        await message.delete()
        return  # Stop further processing

    # ✅ Check if the message exists in bot tracking
    if message.id in bot.messages_to_delete:
        message_data = bot.messages_to_delete[message.id]
        print(f"✅ Found message {message.id} in tracked events.")

        if len(message_data) == 8:  # Old format detected
            print("⚠️ WARNING: Old format detected. Fixing now.")
            message, original_duration, remaining_duration, item_name, rarity_name, color, amount, channel_id, creator_name = message_data
            negative_adjustment = 0  # Assume no negative time for old events
            image_url = None  # Older events don't store images
        else:
            message, original_duration, remaining_duration, negative_adjustment, item_name, rarity_name, color, amount, channel_id, creator_name, image_url = message_data

        current_time = int(time.time())
        event_creation_time = int(message.created_at.timestamp())
        adjusted_remaining_time = max(0, remaining_duration - (current_time - event_creation_time))
        new_message = None  # ✅ Ensure new_message is always defined

        ### 🛠 **Debugging Logs**
        print(f"🛠 DEBUGGING TIME VALUES:")
        print(f"   🕒 Current Time: {current_time}")
        print(f"   📌 Event Created At: {event_creation_time}")
        print(f"   ⏳ Remaining Time: {adjusted_remaining_time} sec ({adjusted_remaining_time//60}m)")
        print(f"   ⏳ Original Duration: {original_duration} sec ({original_duration//60}m)")
        print(f"   🛑 Negative Adjustment: {negative_adjustment} sec ({negative_adjustment//60}m)")

        # ✅ Universal Event Format (for all cases: resets, claims, shares)
        def generate_event_text(actor: str, action: str) -> str:
            """Creates a standardized event message format."""
            return (
                f"{color} **{amount}x {rarity_name} {item_name}** {color}\n"
                f"👤 **{action} by: {actor}**\n"
                f"⏳ **Next spawn at** <t:{new_end_time}:F>\n"
                f"⏳ **Countdown:** <t:{new_end_time}:R>\n"
                f"⏳ **Interval: {original_duration//60}m**"
            )

        # ✅ Reset Event (Restores original interval)
        if reaction_emoji == "✅":
            print(f"🔄 Resetting event: {item_name}")
            new_end_time = current_time + original_duration
            event_text = generate_event_text(user.display_name, "Reset")

        # ✅ Share Event (Removes share reactions, only allows claim)
        elif reaction_emoji in config.GATHERING_CHANNELS:
            new_channel_name = config.GATHERING_CHANNELS[reaction_emoji]
            target_channel = discord.utils.get(guild.channels, name=new_channel_name)

            if target_channel:
                print(f"📤 Sharing event: {item_name} to {new_channel_name}")
                shared_remaining_time = min(adjusted_remaining_time, original_duration)
                new_end_time = current_time + shared_remaining_time
                event_text = generate_event_text(user.display_name, "Shared")
                channel = target_channel  # ✅ Set channel to new location

        # ✅ Claim Event (Moves to Personal Channel)
        elif reaction_emoji == "📥":
            print(f"📥 Claiming event: {item_name} for {user.display_name}")

            user_channel_name = user.display_name.lower().replace(" ", "-")
            personal_category = next((cat for cat in guild.categories if cat.name.lower() == "personal intel"), None)

            if not personal_category:
                print(f"❌ ERROR: 'PERSONAL INTEL' category not found!")
                return

            user_channel = discord.utils.get(guild.text_channels, name=user_channel_name, category=personal_category)

            if not user_channel:
                print(f"📌 Creating personal channel for {user.display_name}")
                user_channel = await guild.create_text_channel(name=user_channel_name, category=personal_category)

            new_end_time = current_time + adjusted_remaining_time
            event_text = generate_event_text(user.display_name, "Claimed")
            channel = user_channel  # ✅ Set channel to personal location

        else:
            return  # ✅ If the reaction is not handled, stop execution

        # ✅ Send New Event Message
        embed = discord.Embed()
        if image_url:
            embed.set_image(url=image_url)

        new_message = await channel.send(event_text, embed=embed if image_url else None)

        # ✅ Add Reactions
        await new_message.add_reaction("✅")
        await new_message.add_reaction("🗑️")
        await new_message.add_reaction("📥")  # ✅ Always allow claiming
        await new_message.add_reaction("🔔")  # ✅ Bell reaction for pings
        
        # ✅ If event is shared, REMOVE sharing reactions (⛏️, 🌲, 🌿, etc.)
        if reaction_emoji in config.GATHERING_CHANNELS:
            print(f"📌 Event moved to a shared channel, replacing share options with claim (`📥`).")
        else:
            for emoji in config.GATHERING_CHANNELS.keys():
                await new_message.add_reaction(emoji)

        # ✅ Store New Event Data
        bot.messages_to_delete[new_message.id] = (
            new_message, original_duration, adjusted_remaining_time, negative_adjustment,
            item_name, rarity_name, color, amount, new_message.channel.id, creator_name, image_url
        )

        await message.delete()  # ✅ Remove old message
