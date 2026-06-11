import discord
from discord.ext import commands
import os
import sys

# Add parent directory to sys.path to import config and ide_gateway_cog
WORKSPACE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_PATH not in sys.path:
    sys.path.append(WORKSPACE_PATH)

from bot.config import AUTHORIZED_USER_ID, DISCORD_BOT_TOKEN
try:
    from bot.config import TARGET_CHANNEL_NAME
except ImportError:
    TARGET_CHANNEL_NAME = "my-project-channel" # [USER_FILL_REQUIRED] Channel name to listen to

from bot.ide_gateway_cog import IDEGatewayCore

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Config for the core
gateway_config = {
    "authorized_user_id": AUTHORIZED_USER_ID,
    "target_channel_name": TARGET_CHANNEL_NAME,
    "ai_tasks_file": os.path.join(WORKSPACE_PATH, "bot", "ai_tasks.txt"),
    "ai_reply_file": os.path.join(WORKSPACE_PATH, "bot", "ai_reply.txt"),
    "workspace_path": WORKSPACE_PATH
}

@bot.event
async def setup_hook():
    await bot.add_cog(IDEGatewayCore(bot, config=gateway_config))

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
