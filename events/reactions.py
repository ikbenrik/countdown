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
        await track_ping_reaction(bot, payload)  # ✅ Add user to ping list

    # ✅ Remove user from pings if they remove 🔔 reaction
    if payload.event_type == "REACTION_REMOVE" and reaction_emoji == "🔔":
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

        ### 🛠 **Debugging Logs**
        print(f"🛠 DEBUGGING TIME VALUES:")
        print(f"   🕒 Current Time: {current_time}")
        print(f"   📌 Event Created At: {event_creation_time}")
        print(f"   ⏳ Remaining Time: {adjusted_remaining_time} sec ({adjusted_remaining_time//60}m)")
        print(f"   ⏳ Original Duration: {original_duration} sec ({original_duration//60}m)")
        print(f"   🛑 Negative Adjustment: {negative_adjustment} sec ({negative_adjustment//60}m)")

        # ✅ Reset Event (Restores original interval)
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

            embed = discord.Embed()
            if image_url:
                embed.set_image(url=image_url)

            new_message = await channel.send(reset_text, embed=embed if image_url else None)

            await new_message.add_reaction("✅")
            await new_message.add_reaction("🗑️")
            await new_message.add_reaction("🔔")  # ✅ Bell reaction for pings

            for emoji in config.GATHERING_CHANNELS.keys():
                await new_message.add_reaction(emoji)

            bot.messages_to_delete[new_message.id] = (
                new_message, original_duration, original_duration, 0, item_name, rarity_name, color, amount, channel_id, creator_name, image_url
            )
            await message.delete()

        # ✅ Delete Event
        elif reaction_emoji == "🗑️":
            print(f"🗑️ Deleting event: {item_name}")
            await message.delete()
            del bot.messages_to_delete[message.id]

        # ✅ Share Event (Maintains Timer)
        elif reaction_emoji in config.GATHERING_CHANNELS:
            new_channel_name = config.GATHERING_CHANNELS[reaction_emoji]
            target_channel = discord.utils.get(guild.channels, name=new_channel_name)

            if target_channel:
                print(f"📤 Sharing event: {item_name} to {new_channel_name}")

                shared_remaining_time = min(adjusted_remaining_time, original_duration)
                new_end_time = current_time + shared_remaining_time

                shared_text = (
                    f"{color} **{amount}x {rarity_name} {item_name}** {color}\n"
                    f"👤 **Shared by: {user.display_name}**\n"
                    f"⏳ **Next spawn at** <t:{new_end_time}:F>\n"
                    f"⏳ **Countdown:** <t:{new_end_time}:R>\n"
                    f"⏳ **Interval: {original_duration//60}m**"
                )

                embed = discord.Embed()
                if image_url:
                    embed.set_image(url=image_url)

                new_message = await target_channel.send(shared_text, embed=embed if image_url else None)

                await new_message.add_reaction("✅")
                await new_message.add_reaction("🗑️")
                await new_message.add_reaction("📥")
                await new_message.add_reaction("🔔")  # ✅ Bell reaction for pings

                bot.messages_to_delete[new_message.id] = (
                    new_message, original_duration, shared_remaining_time, negative_adjustment, 
                    item_name, rarity_name, color, amount, target_channel.id, creator_name, image_url
                )
                await message.delete()

        # ✅ Claim Event (Move to Personal Channel)
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

            new_message = await user_channel.send(shared_text, embed=embed if image_url else None)

            await new_message.add_reaction("✅")
            await new_message.add_reaction("🗑️")
            await new_message.add_reaction("🔔")  # ✅ Bell reaction for pings
            for emoji in config.GATHERING_CHANNELS.keys():
                await new_message.add_reaction(emoji)

            await message.delete()
