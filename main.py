import os

import google.generativeai as genai
import discord

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
gemini_agent_cog = AgentCog(gemini_agent)

# create intents object for discord bot initialization
intents = discord.Intents.default()
intents.message_content = True

# create bot instance
bot = commands.Bot(command_prefix="$", intents=intents)


@bot.event
async def on_ready():
    await bot.add_cog(gemini_agent_cog)
    print("Gemini bot is online")


@bot.command(name="generate", description="generate content using gemini")
async def generate(ctx, prompt: str):
    content = None
    try:
        content = gemini_agent.generate_content(prompt)
    except ValueError as e:
        content = e.__repr__()

    await ctx.send(f"Hi {ctx.author.name}. Your content as requested:\n{content}")


if __name__ == "__main__":
    bot.run(token=DISCORD_TOKEN)
