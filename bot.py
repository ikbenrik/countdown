import discord
from discord.ext import commands
import config
from commands.countdown import cd
from events.reactions import handle_reaction
from commands.items import add_item, remove_item, list_items  # ✅ Import all item commands
from events.ping_manager import schedule_pings  # ✅ Fixed Import
import asyncio
import logging

# ✅ Reset logging completely
logging.basicConfig(
    level=logging.DEBUG,  # 🔥 Set to DEBUG mode
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot_debug.log"),  # ✅ Save logs in a separate file
        logging.StreamHandler()  # ✅ Print logs in the terminal
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
async def on_raw_reaction_add(payload):
    """Handles reaction events, including bulk deletion for !list and error messages."""
    print(f"🔎 DEBUG: Reaction detected: {payload.emoji.name} by User ID {payload.user_id}")

    if payload.emoji.name == "🗑️":
        guild = bot.get_guild(payload.guild_id)
        channel = bot.get_channel(payload.channel_id)

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return  # ✅ Message was already deleted

        # ✅ Delete messages from !list or error handling
        if hasattr(bot, "list_messages_to_delete") and message.id in [msg.id for msg in bot.list_messages_to_delete]:
            for msg in bot.list_messages_to_delete:
                try:
                    await msg.delete()
                except discord.NotFound:
                    continue
                except discord.Forbidden:
                    print("🚫 Bot does not have permission to delete messages!")
                    return
            bot.list_messages_to_delete = []
            return

        # ✅ Handle deleting error messages and original wrong commands
        if hasattr(bot, "error_messages") and message.id in bot.error_messages:
            command_message = bot.error_messages[message.id]
            try:
                await command_message.delete()  # ✅ Delete the original command
                await message.delete()  # ✅ Delete the error message
                del bot.error_messages[message.id]  # ✅ Remove from tracking
            except discord.NotFound:
                pass
            except discord.Forbidden:
                print("🚫 Bot lacks permissions to delete error messages!")

    # ✅ Handle other reactions normally
    await handle_reaction(bot, payload)

@bot.event
async def on_ready():
    """Ensures the bot is ready and starts background tasks."""
    if not hasattr(bot, "messages_to_delete"):
        bot.messages_to_delete = {}

    if not hasattr(bot, "list_messages_to_delete"):
        bot.list_messages_to_delete = []

    if not hasattr(bot, "error_messages"):
        bot.error_messages = {}  # ✅ Track error messages

    print(f"✅ Logged in as {bot.user}")
    print("✅ Bot is running and ready for reactions!")

    # ✅ Start the ping scheduler
    bot.loop.create_task(schedule_pings(bot))

# ✅ Start bot
bot.run(config.TOKEN)
