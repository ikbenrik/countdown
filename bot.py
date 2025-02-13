import discord
from discord.ext import commands
import config
from commands.countdown import cd
from events.reactions import handle_reaction
from commands.items import add_item, remove_item, list_items  # ✅ Import all item commands
from events.ping_manager import schedule_pings  # ✅ Fixed Import
import asyncio
import logging
from commands.bosses import add_boss, get_bosses, list_all_bosses
from commands.bosses import add_boss, get_bosses, list_all_bosses, find_boss  # ✅ Import find_boss function

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

@bot.command(name="b")
async def command_b(ctx, action: str = None, dungeon: str = None, boss_name: str = None, time: str = None):
    """Handles boss & dungeon management or listing."""

    if action is None:  
        await list_all_bosses(ctx)
        return

    if action.lower() == "list":  
        await list_all_bosses(ctx)
        return

    if action.lower() == "add":
        if not dungeon:
            error_msg = await ctx.send("❌ **You must specify a dungeon!** Use `!b add <dungeon>` or `!b add <dungeon> <boss> <time>`.")
            await error_msg.add_reaction("🗑️")
            return
        await add_boss(ctx, dungeon, boss_name, time)
        return

    # ✅ Check if the user typed a boss name
    found_boss = await find_boss(ctx, action)  
    if found_boss:
        return

    # ✅ If `!b <dungeon>` is used, create events for all bosses in that dungeon
    await get_bosses(ctx, action)

    # ✅ If it's a boss, create a countdown
    found_boss = await find_boss(ctx, action)  # ✅ Check if it's a boss
    if found_boss:
        return

    await ctx.send("❌ **Invalid command!**")


    # ✅ If `!b <dungeon>` is typed, create events for all bosses in that dungeon
    if action and dungeon is None and boss_name is None and time is None:
        found_dungeon = await get_bosses(ctx, action)  # ✅ Check if it's a dungeon
        if not found_dungeon:
            found_boss = await find_boss(ctx, action)  # ✅ Check if it's a boss
            if not found_boss:
                error_msg = await ctx.send(f"❌ **Dungeon or Boss `{action.capitalize()}` not found!** Use `!b add <dungeon>` to create one.")
                await error_msg.add_reaction("🗑️")
        return

    # ✅ If user types an invalid command
    error_msg = await ctx.send("❌ **Invalid command!** Use `!b add <dungeon> [boss] [time]`, `!b list` to list everything, or `!b <dungeon>` to create events for bosses.")
    await error_msg.add_reaction("🗑️")

    # ✅ If `!b <dungeon>` is typed, create events for all bosses in that dungeon
    if action and dungeon is None and boss_name is None and time is None:
        await get_bosses(ctx, action)  # ✅ Use the first argument as the dungeon name
        return

    # ✅ If user types an invalid command
    error_msg = await ctx.send("❌ **Invalid command!** Use `!b add <dungeon> [boss] [time]`, `!b list` to list everything, or `!b <dungeon>` to create events for bosses.")
    await error_msg.add_reaction("🗑️")

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
