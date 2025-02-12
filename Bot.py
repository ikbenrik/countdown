import discord  # ✅ Missing import
from discord.ext import commands
import config
from commands.countdown import cd
from events.reactions import handle_reaction

# ✅ Set up intents correctly
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  
intents.messages = True  
intents.guilds = True  
intents.members = True  # Ensure this is included

# ✅ Pass intents when initializing bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Ensures all necessary bot variables are initialized on startup."""
    if not hasattr(bot, "messages_to_delete"):
        bot.messages_to_delete = {}  # ✅ Initialize message tracking dictionary

    print(f"✅ Logged in as {bot.user}")
    print("✅ Bot is ready and listening for reactions!")

@bot.event
async def on_raw_reaction_add(payload):
    """Handles reactions for sharing, claiming, resetting, and deleting timers."""
    await handle_reaction(bot, payload)  # ✅ Ensure this event calls the reaction handler

@bot.command(name="cd")
async def command_cd(ctx, *args):
    await cd(ctx, *args)

bot.run(config.TOKEN)
