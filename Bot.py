import discord
from discord.ext import commands
import config
from commands.countdown import cd
from events.reactions import handle_reaction  # ✅ Import reaction handling

# ✅ Setup intents properly
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  
intents.messages = True  
intents.guilds = True  
intents.members = True  

# ✅ Initialize the bot
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
    """Handles reactions globally."""
    await handle_reaction(bot, payload)  # ✅ Pass bot object to `reactions.py`

@bot.command(name="cd")
async def command_cd(ctx, *args):
    """Handles countdown command execution."""
    await cd(ctx, *args)

# ✅ Run the bot
bot.run(config.TOKEN)
