import os

import google.generativeai as genai
import discord

from logger import logger
from discord.ext import commands
from agent import Agent, AgentCog

# grab api keys from environment
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# configure google genai
genai.configure(api_key=GOOGLE_API_KEY)

# initialize Agent instance for content generation
gemini_agent = Agent(model_name="gemini-1.0-pro-latest", daily_limit=1500)
# initialize AgentCog instance for scheduling tasks related to the agent
gemini_agent_cog = AgentCog(gemini_agent, 6)

# create intents object for discord bot initialization
intents = discord.Intents.default()
intents.message_content = True

# create bot instance
bot = commands.Bot(command_prefix="$", intents=intents)


@bot.event
async def on_ready():
    await bot.add_cog(gemini_agent_cog)
    logger.info("Gemini bot is online")


@bot.event
async def on_message(message: discord.Message):
    username = message.author

    # ignore messages created by the bot itself
    if username == bot.user:
        return

    prompt = message.content

    try:
        content = gemini_agent.send_chat(username, prompt)
        logger.info(
            "Chat request completed",
            extra=dict(username=username, prompt=prompt, response_length=len(content)),
        )
        await message.reply(f"{content}")
    except Exception as e:
        content = str(e)
        logger.error(
            "An exception occured when requesting for content.",
            extra=dict(exception=content),
        )
        await message.reply(f"There was an exception. {content}")


if __name__ == "__main__":
    bot.run(token=DISCORD_TOKEN)
