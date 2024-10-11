import os
import asyncio

import discord
import google.generativeai as genai
from dotenv import load_dotenv
from agent import GeminiAgent
from bot import Bot, BotCog

load_dotenv()
# grab api keys from environment
OWNER = os.getenv("BOT_OWNER")
# how long the chat will live since last message
CHAT_TTL = int(os.getenv("CHAT_TTL"))
# gemini agent model configurations
MODEL = os.getenv("MODEL")
ACCEPTED_MODELS = os.getenv("ACCEPTED_MODELS").split(",")
# daily request limit
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# configure google genai
genai.configure(api_key=GOOGLE_API_KEY)

# initialize gemini agent instance for content generation
gemini_agent = GeminiAgent(
    model_name=MODEL, daily_limit=DAILY_LIMIT, accepted_models=ACCEPTED_MODELS
)

# create intents object for discord bot initialization
intents = discord.Intents.default()
intents.message_content = True

# create bot instance
bot = Bot(OWNER, gemini_agent, command_prefix="$", intents=intents)
# initialize BogCog instance for bot commands and scheduled tasks
bot_cog = BotCog(bot, CHAT_TTL)
# register the cog
asyncio.run(bot.add_cog(bot_cog))

if __name__ == "__main__":
    # run the bot
    bot.run(token=DISCORD_TOKEN)
