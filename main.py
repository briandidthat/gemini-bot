import os
from datetime import timedelta
import asyncio

import discord
import google.generativeai as genai

from agent import Agent, AgentCog
from bot import Bot, BotCog


# grab api keys from environment
BOT_OWNER = os.getenv("BOT_OWNER")
CHAT_TTL = float(os.getenv("CHAT_TTL"))
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# configure google genai
genai.configure(api_key=GOOGLE_API_KEY)

# initialize Agent instance for content generation
gemini_agent = Agent(model_name="gemini-pro-vision", daily_limit=DAILY_LIMIT)
# initialize AgentCog instance for scheduling tasks related to the agent
gemini_agent_cog = AgentCog(gemini_agent, timedelta(days=CHAT_TTL))

# create intents object for discord bot initialization
intents = discord.Intents.default()
intents.message_content = True

# create bot instance
bot = Bot(gemini_agent=gemini_agent, command_prefix="$", intents=intents)
# initialize BogCog instance for bot commands
bot_cog = BotCog(bot, BOT_OWNER)


# register the cogs with the bot
async def register():
    await bot.add_cog(bot_cog)
    await bot.add_cog(gemini_agent_cog)


if __name__ == "__main__":
    # run the coroutine to register the cogs
    asyncio.run(register())
    # run the bot
    bot.run(token=DISCORD_TOKEN)
