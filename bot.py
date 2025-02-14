import discord
from discord.ext import commands
import config
from commands.countdown import cd
from events.reactions import handle_reaction
from commands.items import add_item, remove_item, list_items  # ✅ Import all item commands
from events.ping_manager import schedule_pings  # ✅ Fixed Import
import asyncio
import logging
from commands.bosses import add_boss, get_bosses, list_all_bosses, find_boss, bosses_data, load_bosses

bosses_data = load_bosses()

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

    # ✅ **Try to delete the user’s command message**
    try:
        await ctx.message.delete()
    except discord.NotFound:
        print("⚠️ Warning: Command message was already deleted.")
    except discord.Forbidden:
        print("🚫 Bot does not have permission to delete messages in this channel!")
        return

    if action.lower() == "list":
        await list_all_bosses(ctx)
        return  # 🚀 **Ensure it stops execution after listing**

    # ✅ **Try to delete the user’s command message**
    try:
        await ctx.message.delete()
    except discord.NotFound:
        print("⚠️ Warning: Command message was already deleted.")
    except discord.Forbidden:
        print("🚫 Bot does not have permission to delete messages in this channel!")
        return
 
    if action.lower() == "add":
        if not dungeon:
            error_msg = await ctx.send("❌ **You must specify a dungeon!** Use `!b add <dungeon>` or `!b add <dungeon> <boss> <time>`.")
            await error_msg.add_reaction("🗑️")
            
            try:
                await ctx.message.delete()
            except discord.NotFound:
                print("⚠️ Warning: Command message was already deleted.")
            except discord.Forbidden:
                print("🚫 Bot does not have permission to delete messages in this channel!")
            return
            
        await add_boss(ctx, dungeon, boss_name, time)

    try:
        await ctx.message.delete()
    except discord.NotFound:
        print("⚠️ Warning: Command message was already deleted.")
    except discord.Forbidden:
        print("🚫 Bot does not have permission to delete messages in this channel!")
        return

    # ✅ First, check if it's a dungeon
    found_dungeon = action.lower() in bosses_data
    if found_dungeon:
        await get_bosses(ctx, action)  # ✅ Create events for all bosses in that dungeon
        return  # ✅ Prevent looping

    # ✅ If it's NOT a dungeon, check if it's a boss
    found_boss = await find_boss(ctx, action)
    if found_boss:
        return  # ✅ Prevent looping

    # ❌ If neither a dungeon nor a boss is found
    error_msg = await ctx.send(f"❌ **Dungeon or Boss `{action.capitalize()}` not found!** Try `!b list` to see all available options.")
    await error_msg.add_reaction("🗑️")

    found_boss = await find_boss(ctx, action)  
    if found_boss:
        return

    await get_bosses(ctx, action)

    found_boss = await find_boss(ctx, action)  # ✅ Check if it's a boss
    if found_boss:
        return

    await ctx.send("❌ **Invalid command!**")

    if action and dungeon is None and boss_name is None and time is None:
        found_dungeon = await get_bosses(ctx, action)  # ✅ Check if it's a dungeon
        if not found_dungeon:
            found_boss = await find_boss(ctx, action)  # ✅ Check if it's a boss
            if not found_boss:
                error_msg = await ctx.send(f"❌ **Dungeon or Boss `{action.capitalize()}` not found!** Use `!b add <dungeon>` to create one.")
                await error_msg.add_reaction("🗑️")
        return

    error_msg = await ctx.send("❌ **Invalid command!** Use `!b add <dungeon> [boss] [time]`, `!b list` to list everything, or `!b <dungeon>` to create events for bosses.")
    await error_msg.add_reaction("🗑️")

    if action and dungeon is None and boss_name is None and time is None:
        await get_bosses(ctx, action)  # ✅ Use the first argument as the dungeon name
        return

    error_msg = await ctx.send("❌ **Invalid command!** Use `!b add <dungeon> [boss] [time]`, `!b list` to list everything, or `!b <dungeon>` to create events for bosses.")
    await error_msg.add_reaction("🗑️")

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

@bot.event
async def on_ready():
    """Ensures the bot is ready and starts background tasks."""
    if not hasattr(bot, "messages_to_delete"):
        bot.messages_to_delete = {}  # ✅ Ensure message tracking works

    if not hasattr(bot, "list_messages_to_delete"):
        bot.list_messages_to_delete = []  # ✅ Ensure list message tracking works

    print(f"✅ Logged in as {bot.user}")
    print("✅ Bot is running and ready for reactions!")

    # ✅ Start the ping scheduler
    bot.loop.create_task(schedule_pings(bot))

# ✅ Start bot
bot.run(config.TOKEN)
