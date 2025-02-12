from discord.ext import commands
import config
from commands.countdown import cd
from events.reactions import handle_reaction

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    """Ensures all necessary bot variables are initialized on startup."""
    if not hasattr(bot, "messages_to_delete"):
        bot.messages_to_delete = {}  # ✅ Initialize message tracking dictionary

    print(f"✅ Logged in as {bot.user}")
    print("✅ Bot is ready and listening for reactions!")


@bot.command(name="cd")
async def command_cd(ctx, *args):
    await cd(ctx, *args)

bot.run(config.TOKEN)
