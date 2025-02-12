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
            message, original_duration, remaining_duration, item_name, rarity_name, color, amount, channel_id, creator_name = message_data
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

        # ✅ Share Event (Must Keep Remaining Time + Negative Adjustment)
        elif reaction_emoji in config.GATHERING_CHANNELS:
            new_channel_name = config.GATHERING_CHANNELS[reaction_emoji]
            target_channel = discord.utils.get(guild.channels, name=new_channel_name)

            if target_channel:
                print(f"📤 Sharing event: {item_name} to {new_channel_name}")

                # ✅ Ensure the correct time is applied when sharing
                if negative_adjustment > 0:
                    # If a negative adjustment was originally applied, retain it
                    shared_remaining_time = max(0, adjusted_remaining_time)  # Use adjusted remaining time
                else:
                    # If no negative time was set, just use the true remaining time
                    shared_remaining_time = max(0, remaining_duration - (current_time - event_creation_time))

                # ✅ Ensure it never resets to the full interval when sharing
                shared_remaining_time = min(shared_remaining_time, original_duration)
                new_end_time = current_time + shared_remaining_time

                # 🟢 Debugging to confirm correct values
                print(f"🟢 DEBUG - Final Sharing Time:")
                print(f"   ⏳ Shared Remaining Time: {shared_remaining_time} sec ({shared_remaining_time//60}m)")
                print(f"   📌 New End Time: <t:{new_end_time}:F>")

                # ✅ Prepare the shared message with correct remaining time
                shared_text = (
                    f"{color} **{amount}x {rarity_name} {item_name}** {color}\n"
                    f"👤 **Shared by: {user.display_name}**\n"
                    f"⏳ **Next spawn at** <t:{new_end_time}:F>\n"
                    f"⏳ **Countdown:** <t:{new_end_time}:R>\n"
                    f"⏳ **Interval: {original_duration//60}m**"
                )

                # ✅ Send the corrected shared message
                new_message = await target_channel.send(shared_text)

                # ✅ **Fix: Ensure reactions are added**
                await new_message.add_reaction("✅")  # Reset
                await new_message.add_reaction("🗑️")  # Delete
                await new_message.add_reaction("📥")  # Claim reaction in shared channels

                # ✅ Track new message with the **correct remaining time**
                bot.messages_to_delete[new_message.id] = (
                    new_message, original_duration, shared_remaining_time, negative_adjustment, 
                    item_name, rarity_name, color, amount, target_channel.id, creator_name
                )

                # ✅ Delete the original message after sharing
                await message.delete()
