import os
import json
import discord
import time
import re
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ✅ Enable intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  
intents.messages = True  
intents.guilds = True  
intents.members = True  

# ✅ Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ Load & Save Functions for Items
ITEMS_FILE = "items.json"

def load_items():
    """Load items from a JSON file."""
    if os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return {key.lower().strip(): value for key, value in data.items()}  
            except json.JSONDecodeError:
                print("❌ ERROR: Could not decode JSON file.")
                return {}
    else:
        print(f"❌ ERROR: {ITEMS_FILE} not found.")
    return {}

# ✅ Load saved items on startup
item_timers = load_items()

# ✅ Define shared gathering channels
GATHERING_CHANNELS = {
    "⛏️": "⛏mining-2hours",
    "🌲": "🌲woodcutting-4hours",
    "🌿": "🌿herbalism-4hours"
}

# ✅ Define rarity colors
RARITY_COLORS = {
    "c": ("Common", "⚪"), 
    "u": ("Uncommon", "🟢"), 
    "r": ("Rare", "🔵"), 
    "h": ("Heroic", "🟡"),  
    "e": ("Epic", "🟣"),    
    "l": ("Legendary", "🟠") 
}

@bot.event
async def on_ready():
    """Ensures all necessary bot variables are initialized on startup."""
    bot.messages_to_delete = {}

    print(f"✅ Loaded {len(item_timers)} items from items.json:")
    print(json.dumps(item_timers, indent=4, ensure_ascii=False))  
    print(f"✅ Logged in as {bot.user}")

@bot.command(name="cd")
async def cd(ctx, *args):
    """Handles tracking events with the new command structure."""
    global item_timers

    if len(args) < 1:
        await ctx.send("❌ **Invalid format!** Use `!cd <item> [rarity/amount] [time] [-X minutes]`.")
        return

    item_name = args[0].lower().strip()
    duration = None
    rarity = "r"
    amount = ""
    past_offset = 0  # Default to no past offset

    duration_mapping = {"h": 3600, "m": 60, "s": 1}
    for arg in args[1:]:
        if arg[-1].lower() in duration_mapping and arg[:-1].isdigit():
            duration = int(arg[:-1]) * duration_mapping[arg[-1].lower()]
            continue

        if any(char in "curhel" for char in arg.lower()) and any(char.isdigit() for char in arg):
            rarity_letter = [char for char in arg.lower() if char in "curhel"]
            amount = "".join(filter(str.isdigit, arg))
            rarity = rarity_letter[0] if rarity_letter else "r"
            continue

        if arg.startswith("-") and arg[1:].isdigit():
            past_offset = int(arg[1:]) * 60  # Convert minutes to seconds

    rarity_name, color = RARITY_COLORS.get(rarity, ("Rare", "🔵"))

    if duration is None:
        if item_name in item_timers:
            duration = item_timers[item_name]
        else:
            await ctx.send(f"❌ **{item_name.capitalize()}** is not stored! Use `!cd {item_name} <time>` first.")
            return

    countdown_time = int(time.time()) + duration - past_offset

    countdown_text = (
        f"{color} **{amount}x {rarity_name} {item_name.capitalize()}** {color}\n"
        f"👤 **Posted by: {ctx.author.display_name}**\n"
        f"⏳ **Next spawn at** <t:{countdown_time}:F>\n"
        f"⏳ **Countdown:** <t:{countdown_time}:R>\n"
        f"⏳ **Interval: {duration // 3600}h**"
    )

    countdown_message = await ctx.send(countdown_text)

    await countdown_message.add_reaction("✅")
    await countdown_message.add_reaction("🗑️")
    for emoji in GATHERING_CHANNELS.keys():
        await countdown_message.add_reaction(emoji)

    bot.messages_to_delete[countdown_message.id] = (
        countdown_message, duration, item_name.capitalize(), rarity_name, color, amount, ctx.channel.id, ctx.author.display_name
    )

    await ctx.message.delete()

@bot.event
async def on_raw_reaction_add(payload):
    """Handles reactions for sharing, claiming, resetting, and deleting timers."""
    if payload.user_id == bot.user.id:
        return  

    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)

    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.NotFound:
        return  

    user = guild.get_member(payload.user_id)
    if not user:
        return

    message_id = payload.message_id
    reaction_emoji = str(payload.emoji)

    print(f"🔍 Reaction detected: {reaction_emoji} by {user.display_name}")

    if message_id in bot.messages_to_delete:
        message_data = bot.messages_to_delete[message_id]
        if not message_data:
            return

        message, stored_duration, item_name, rarity_name, color, amount, channel_id, creator_name = message_data

        # ✅ Extract original duration
        original_duration_match = re.search(r"⏳ \*\*Interval: (\d+)h\*\*", message.content)
        original_duration = int(original_duration_match.group(1)) * 3600 if original_duration_match else stored_duration

        current_time = int(time.time())

        if reaction_emoji == "✅":
            """🔄 Reset event - Uses original duration"""
            print(f"🔄 Resetting event: {item_name}")

            new_end_time = current_time + original_duration

            reset_text = (
                f"{color} **{amount}x {rarity_name} {item_name}** {color}\n"
                f"👤 **Reset by: {user.display_name}**\n"
                f"⏳ **Next spawn at** <t:{new_end_time}:F>\n"
                f"⏳ **Countdown:** <t:{new_end_time}:R>\n"
                f"⏳ **Interval: {original_duration // 3600}h**"
            )

            new_message = await channel.send(reset_text)

            await new_message.add_reaction("✅")
            await new_message.add_reaction("🗑️")
            for emoji in GATHERING_CHANNELS.keys():
                await new_message.add_reaction(emoji)

            bot.messages_to_delete[new_message.id] = (
                new_message, original_duration, item_name, rarity_name, color, amount, channel.id, creator_name
            )

            await message.delete()
            del bot.messages_to_delete[message_id]

# ✅ Run the bot
bot.run(TOKEN)
