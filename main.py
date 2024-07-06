import os
import asyncio

import discord
import google.generativeai as genai

from agent import GeminiAgent
from bot import Bot, BotCog


# grab api keys from environment
OWNER = os.getenv("BOT_OWNER")
CHAT_TTL = float(os.getenv("CHAT_TTL"))
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# configure google genai
genai.configure(api_key=GOOGLE_API_KEY)

# initialize gemini agent instance for content generation
gemini_agent = GeminiAgent(
    model_name="gemini-1.5-flash-latest", daily_limit=DAILY_LIMIT
)

# create intents object for discord bot initialization
intents = discord.Intents.default()
intents.message_content = True

# create bot instance
bot = Bot(OWNER, gemini_agent, command_prefix="$", intents=intents)
# initialize BogCog instance for bot commands and scheduled tasks
bot_cog = BotCog(bot, CHAT_TTL)


# register the cog with the bot
async def register():
    await bot.add_cog(bot_cog)


if __name__ == "__main__":
    # run the coroutine to register the cog
    asyncio.run(register())
    # run the bot
    bot.run(token=DISCORD_TOKEN)
