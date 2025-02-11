import os
import json
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

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
