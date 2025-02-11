from discord.ext import commands
import config
from commands.countdown import cd
from events.reactions import handle_reaction

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_raw_reaction_add(payload):
    await handle_reaction(bot, payload)

@bot.command(name="cd")
async def command_cd(ctx, *args):
    await cd(ctx, *args)

bot.run(config.TOKEN)
