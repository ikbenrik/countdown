import discord
from discord.ext import commands
import config
from commands.countdown import cd
from events.reactions import handle_reaction

# ✅ Setup intents
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
    """Ensures all necessary bot variables are initialized on startup."""
    bot.messages_to_delete = {}  # ✅ Ensure this is properly initialized

    print(f"✅ Logged in as {bot.user}")
    print("✅ Bot is ready and listening for reactions!")

@bot.event
async def on_raw_reaction_add(payload):
    """Handles all reactions on messages."""
    await handle_reaction(bot, payload)  # ✅ Pass bot to reaction handler

@bot.command(name="cd")
async def command_cd(ctx, *args):
    """Handles countdown command execution."""
    await cd(bot, *args)  # ✅ Pass bot so we can store messages correctly
    try:
        await ctx.message.delete()  # ✅ Deletes the original command message
    except discord.NotFound:
        print("⚠️ Warning: Command message was already deleted.")

# ✅ Start bot
bot.run(config.TOKEN)
