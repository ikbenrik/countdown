import discord
import config
import time
import logging

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

    # ✅ Check if the message exists in bot tracking
    if message.id in bot.messages_to_delete:
        message_data = bot.messages_to_delete[message.id]
        print(f"✅ Found message {message.id} in tracked events.")

        if len(message_data) == 8:  # Old format detected
            print("⚠️ WARNING: Old format detected. Fixing now.")
            message, original_duration, item_name, rarity_name, color, amount, channel_id, creator_name = message_data
            remaining_duration = original_duration
            negative_adjustment = 0  # Assume no negative time for old events
        else:
            message, original_duration, remaining_duration, negative_adjustment, item_name, rarity_name, color, amount, channel_id, creator_name = message_data

        current_time = int(time.time())
        event_creation_time = int(message.created_at.timestamp())
        adjusted_remaining_time = max(0, remaining_duration - (current_time - event_creation_time))

        ### 🛠 **Debugging Logs**
        print(f"🛠 DEBUGGING TIME VALUES:")
        print(f"   🕒 Current Time: {current_time}")
        print(f"   📌 Event Created At: {event_creation_time}")
        print(f"   ⏳ Remaining Time: {adjusted_remaining_time} sec ({adjusted_remaining_time//60}m)")
        print(f"   ⏳ Original Duration: {original_duration} sec ({original_duration//60}m)")
        print(f"   🛑 Negative Adjustment (Should be Non-Zero if Set): {negative_adjustment} sec ({negative_adjustment//60}m)")

        # ✅ Reset Event (Always restores original interval)
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

            if channel.name in config.GATHERING_CHANNELS.values():
                await new_message.add_reaction("📥")
            else:
                for emoji in config.GATHERING_CHANNELS.keys():
                    await new_message.add_reaction(emoji)

            bot.messages_to_delete[new_message.id] = (
                new_message, original_duration, original_duration, 0, item_name, rarity_name, color, amount, channel_id, creator_name
            )
            await message.delete()

        # ✅ Delete Event
        elif reaction_emoji == "🗑️":
            print(f"🗑️ Deleting event: {item_name}")
            await message.delete()
            del bot.messages_to_delete[message.id]

        # ✅ Claim Event (📥 Moves event to personal channel)
        elif reaction_emoji == "📥":
            print(f"📥 Claiming event: {item_name} for {user.display_name}")

            # ✅ Find or Create "Personal Intel" category
            personal_category = discord.utils.get(guild.categories, name="Personal Intel")
            if not personal_category:
                print("❌ ERROR: 'Personal Intel' category not found!")
                return  # Don't proceed without a category

            # ✅ Ensure the personal channel exists (lowercase)
            user_channel_name = user.display_name.lower().replace(" ", "-")
            user_channel = discord.utils.get(guild.text_channels, name=user_channel_name)

            # ✅ If the personal channel doesn't exist, create it
            if not user_channel:
                print(f"🆕 Creating personal channel: {user_channel_name}")

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
                }

                user_channel = await guild.create_text_channel(
                    name=user_channel_name,
                    category=personal_category,
                    overwrites=overwrites
                )

            # ✅ Ensure the correct time is applied when claiming
            claimed_remaining_time = max(0, adjusted_remaining_time + negative_adjustment)
            claimed_remaining_time = min(claimed_remaining_time, original_duration)
            new_end_time = current_time + claimed_remaining_time

            print(f"🟢 DEBUG - Claiming Event with:")
            print(f"   ⏳ Claimed Remaining Time: {claimed_remaining_time} sec ({claimed_remaining_time//60}m)")
            print(f"   📌 New End Time: <t:{new_end_time}:F>")

            # ✅ Format claimed event text
            claimed_text = (
                f"{color} **{amount}x {rarity_name} {item_name}** {color}\n"
                f"👤 **Claimed by: {user.display_name}**\n"
                f"⏳ **Next spawn at** <t:{new_end_time}:F>\n"
                f"⏳ **Countdown:** <t:{new_end_time}:R>\n"
                f"⏳ **Interval: {original_duration//60}m**"
            )

            # ✅ Post in personal channel
            new_message = await user_channel.send(claimed_text)
            await new_message.add_reaction("✅")  # Reset
            await new_message.add_reaction("🗑️")  # Delete
            await new_message.add_reaction("⛏️")  # Re-share option

            # ✅ Store new message details
            bot.messages_to_delete[new_message.id] = (
                new_message, original_duration, claimed_remaining_time, 0, item_name, rarity_name, color, amount, user_channel.id, user.display_name
            )

            # ✅ Delete the original message from the shared channel
            await message.delete()

        # ✅ Share Event (Must Keep Remaining Time + Negative Adjustment)
        elif reaction_emoji in config.GATHERING_CHANNELS:
            new_channel_name = config.GATHERING_CHANNELS[reaction_emoji]
            target_channel = discord.utils.get(guild.channels, name=new_channel_name)

            if target_channel:
                print(f"📤 Sharing event: {item_name} to {new_channel_name}")

                shared_remaining_time = max(0, adjusted_remaining_time + negative_adjustment)
                shared_remaining_time = min(shared_remaining_time, original_duration)
                new_end_time = current_time + shared_remaining_time

                print(f"🟢 DEBUG - Final Sharing Time:")
                print(f"   ⏳ Shared Remaining Time: {shared_remaining_time} sec ({shared_remaining_time//60}m)")
                print(f"   📌 New End Time: <t:{new_end_time}:F>")

                shared_text = (
                    f"{color} **{amount}x {rarity_name} {item_name}** {color}\n"
                    f"👤 **Shared by: {user.display_name}**\n"
                    f"⏳ **Next spawn at** <t:{new_end_time}:F>\n"
                    f"⏳ **Countdown:** <t:{new_end_time}:R>\n"
                    f"⏳ **Interval: {original_duration//60}m**"
                )

                new_message = await target_channel.send(shared_text)
                await message.delete()
