import discord
from discord.ext import commands
import config
from commands.countdown import cd
from commands.items import add_item, remove_item, list_items  # ✅ Import all item commands
from events.reactions import handle_reaction
from events.ping_manager import schedule_pings  # ✅ Fixed Import
from events.ping_manager import track_ping_reaction, remove_ping_reaction, delete_pings_for_event

import asyncio
import logging

# ✅ Reset logging completely
logging.basicConfig(
    level=logging.INFO,  # 🔥 Lowered from DEBUG to INFO
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot_debug.log"),
        logging.StreamHandler()
    ]
)

logging.info("🚀 Bot is starting...")

# ✅ Setup bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  
intents.messages = True  
intents.guilds = True  
intents.members = True

# ✅ Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Ensures the bot is ready and starts background tasks."""
    
    if not hasattr(bot, "messages_to_delete"):
        bot.messages_to_delete = {}  # ✅ Ensure message tracking works
    if not hasattr(bot, "list_messages_to_delete"):
        bot.list_messages_to_delete = []  # ✅ Ensure list message tracking works
    if not hasattr(bot, "error_messages"):
        bot.error_messages = {}  # ✅ Ensure error message tracking works

    print(f"✅ Logged in as {bot.user}")
    print("✅ Bot is running and ready for reactions!")
    
    # ✅ Debugging: List loaded commands
    print("✅ Loaded commands:", [cmd.name for cmd in bot.commands])

    # ✅ Start the ping scheduler
    bot.loop.create_task(schedule_pings(bot))

@bot.event
async def on_raw_reaction_add(payload):
    """Handles reaction events, including bulk deletion for !list messages."""
    print(f"🔎 DEBUG: Reaction detected: {payload.emoji.name} by User ID {payload.user_id}")

    if payload.emoji.name == "🗑️":
        guild = bot.get_guild(payload.guild_id)
        channel = bot.get_channel(payload.channel_id)

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return  # ✅ Message was already deleted

        # ✅ Check if this is an error message needing deletion
        if message.id in bot.error_messages:
            user_message = bot.error_messages.pop(message.id, None)
            if user_message:
                try:
                    await user_message.delete()
                except discord.NotFound:
                    pass  # ✅ User's command message already deleted
            
            try:
                await message.delete()  # ✅ Delete the error message itself
            except discord.NotFound:
                pass
            return
        
        # ✅ Ensure `list_messages_to_delete` exists
        if not hasattr(bot, "list_messages_to_delete"):
            bot.list_messages_to_delete = []

        # ✅ Check if the message is from the bot and is part of the !list output
        if bot.list_messages_to_delete and message.id in [msg.id for msg in bot.list_messages_to_delete]:
            for msg in bot.list_messages_to_delete:
                try:
                    await msg.delete()
                except discord.NotFound:
                    continue  # ✅ Skip if already deleted
                except discord.Forbidden:
                    print("🚫 Bot does not have permission to delete messages!")
                    return
            bot.list_messages_to_delete = []  # ✅ Clear the list after deletion
            return

    # ✅ Handle other reactions normally
    await handle_reaction(bot, payload)

@bot.event
async def on_raw_reaction_remove(payload):
    """Handles reaction removals, including removing users from pings."""
    print(f"🔎 DEBUG: Reaction removed: {payload.emoji.name} by User ID {payload.user_id}")

    if payload.emoji.name == "🔔":
        guild = bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)

        if not user or user.bot:
            return  # ✅ Ignore bots

        await remove_ping_reaction(bot, payload)  # ✅ Remove user from the ping list
        logging.info(f"❌ {user.display_name} removed from pings for event {payload.message_id}")


@bot.command(name="cd")
async def command_cd(ctx, *args):
    """Handles event creation with `!cd` command."""
    if not args:
        error_message = await ctx.send("❌ **Invalid Usage!** Please use `!cd <item_name> <time>`.")
        await error_message.add_reaction("🗑️")  # ✅ Add trash bin reaction
        bot.error_messages[error_message.id] = ctx.message  # ✅ Store error to delete later
        return

    await cd(bot, ctx, *args)  # ✅ Now correctly passing both bot and ctx
    try:
        await ctx.message.delete()  # ✅ Deletes the command message
    except discord.NotFound:
        print("⚠️ Warning: Command message was already deleted.")

@bot.command(name="list")
async def command_list(ctx):
    """Handles listing all items via `!list`"""
    await list_items(ctx)
    try:
        await ctx.message.delete()  # ✅ Delete the user command after execution
    except discord.NotFound:
        print("⚠️ Warning: Command message was already deleted.")

@bot.command(name="add")
async def command_add(ctx, item_name: str, duration: str):
    """Handles adding items via `!add`"""
    await add_item(ctx, item_name, duration)

@bot.command(name="del")
async def command_del(ctx, item_name: str):
    """Handles deleting items via `!del`"""
    await remove_item(ctx, item_name)

# ✅ Start bot
bot.run(config.TOKEN)
