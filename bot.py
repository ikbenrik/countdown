import discord
from discord.ext import commands
import config
from commands.countdown import cd
from events.reactions import handle_reaction

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
    """Ensures the bot is ready."""
    bot.messages_to_delete = {}  # ✅ Ensure message tracking works
    print(f"✅ Logged in as {bot.user}")
    print("✅ Bot is running and ready for reactions!")

@bot.event
async def on_raw_reaction_add(payload):
    """Handles all reactions."""
    await handle_reaction(bot, payload)

@bot.command(name="cd")
async def command_cd(ctx, *args):
    """Handles event creation with `!cd` command."""
    await cd(bot, ctx, *args)
    try:
        await ctx.message.delete()  # ✅ Deletes command message
    except discord.NotFound:
        print("⚠️ Warning: Command message was already deleted.")

# ✅ Start bot
bot.run(config.TOKEN)
