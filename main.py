import os
from datetime import timedelta
import asyncio

import discord
import google.generativeai as genai

from agent import ChatAgent, VisionAgent
from bot import Bot, BotCog


# grab api keys from environment
BOT_OWNER = os.getenv("BOT_OWNER")
CHAT_TTL = float(os.getenv("CHAT_TTL"))
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# configure google genai
genai.configure(api_key=GOOGLE_API_KEY)

# initialize chat agent instance for content generation
chat_agent = ChatAgent(model_name="gemini-1.0-pro-latest")

# initialize vision agent instance for image content generation
vision_agent = VisionAgent(model_name="gemini-pro-vision")

# create intents object for discord bot initialization
intents = discord.Intents.default()
intents.message_content = True

# create bot instance
bot = Bot(chat_agent, vision_agent, DAILY_LIMIT, command_prefix="$", intents=intents)
# initialize BogCog instance for bot commands and scheduled tasks
bot_cog = BotCog(bot, BOT_OWNER, CHAT_TTL)


# register the cog with the bot
async def register():
    await bot.add_cog(bot_cog)


if __name__ == "__main__":
    # run the coroutine to register the cog
    asyncio.run(register())
    # run the bot
    bot.run(token=DISCORD_TOKEN)
