import os
from datetime import timedelta

import discord
import google.generativeai as genai

from agent import Agent, AgentCog
from bot import Bot


# grab api keys from environment
CHAT_TTL = float(os.getenv("CHAT_TTL"))
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# configure google genai
genai.configure(api_key=GOOGLE_API_KEY)

# initialize Agent instance for content generation
gemini_agent = Agent(model_name="gemini-1.0-pro-latest", daily_limit=DAILY_LIMIT)
# initialize AgentCog instance for scheduling tasks related to the agent
gemini_agent_cog = AgentCog(gemini_agent, timedelta(days=CHAT_TTL))

# create intents object for discord bot initialization
intents = discord.Intents.default()
intents.message_content = True

# create bot instance
bot = Bot(gemini_agent, command_prefix="$", intents=intents)


if __name__ == "__main__":
    # add agent cog to bot for scheduling tasks
    bot.add_cog(gemini_agent_cog)
    bot.run(token=DISCORD_TOKEN)
