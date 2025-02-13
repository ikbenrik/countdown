import discord
from discord.ext import commands
import config
from commands.countdown import cd
from events.reactions import handle_reaction
from commands.items import add_item, remove_item, list_items  # ✅ Import all item commands
from events.ping_manager import schedule_pings  # ✅ Fixed Import
import asyncio
import logging
from commands.bosses import add_boss, add_dungeon, get_bosses


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
async def on_ready():
    """Ensures the bot is ready and starts background tasks."""
    bot.messages_to_delete = {}  # ✅ Ensure message tracking works
    print(f"✅ Logged in as {bot.user}")
    print("✅ Bot is running and ready for reactions!")

    # ✅ Start the ping scheduler
    bot.loop.create_task(schedule_pings(bot))

@bot.command(name="b")
async def command_b(ctx, action: str = None, dungeon: str = None, boss_name: str = None, time: str = None):
    """Handles boss & dungeon management or listing."""
    
    if action is None:  # ✅ If no action is provided, list all dungeons
        await get_dungeons(ctx)
        return

    if action.lower() == "list":  # ✅ Show all dungeons & bosses
        await list_all_bosses(ctx)
        return
    
    if action.lower() == "add":
        if not dungeon:
            await ctx.send("❌ **You must specify a dungeon!** Use `!b add <dungeon>` or `!b add <dungeon> <boss> <time>`.")
            return
        
        if not boss_name:  # ✅ If only a dungeon is given, add it
            await add_boss(ctx, dungeon)
            return
        
        if not time:  # ✅ If boss is given without time, return error
            await ctx.send("❌ **You must specify a time for the boss!** Use `!b add <dungeon> <boss> <time>`.")
            return

        await add_boss(ctx, dungeon, boss_name, time)  # ✅ Add boss to dungeon
        return

    # ✅ If only a dungeon is given, show bosses inside
    if not boss_name and not time:
        await get_bosses(ctx, action)  # `action` here is actually the dungeon name
        return
    
    await ctx.send("❌ **Invalid command!** Use `!b add <dungeon> [boss] [time]`, `!b list` to list everything, or `!b <dungeon>` to list bosses.")


    # ✅ If only a dungeon is given, show bosses inside
    if not boss_name and not time:
        await get_bosses(ctx, action)  # `action` here is actually the dungeon name
        return
    
    await ctx.send("❌ **Invalid command!** Use `!b add <dungeon> [boss] [time]` or `!b <dungeon>` to list bosses.")


@bot.event
async def on_raw_reaction_add(payload):
    print(f"🔎 DEBUG: Reaction detected: {payload.emoji.name} by User ID {payload.user_id}")
    await handle_reaction(bot, payload)

@bot.command(name="cd")
async def command_cd(ctx, *args):
    """Handles event creation with `!cd` command."""
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
