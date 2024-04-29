import os
from datetime import timedelta
import discord
from discord.ext import commands
from agent import Agent, AgentCog
from logger import discord_logger

import google.generativeai as genai

# grab api keys from environment
CHAT_TTL = os.getenv("CHAT_TTL")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# configure google genai
genai.configure(api_key=GOOGLE_API_KEY)

# initialize Agent instance for content generation
gemini_agent = Agent(model_name="gemini-1.0-pro-latest", daily_limit=1500)
# initialize AgentCog instance for scheduling tasks related to the agent
gemini_agent_cog = AgentCog(gemini_agent, timedelta(days=float(CHAT_TTL)))

# create intents object for discord bot initialization
intents = discord.Intents.default()
intents.message_content = True

# create bot instance
bot = commands.Bot(command_prefix="$", intents=intents)


@bot.event
async def on_ready():
    await bot.add_cog(gemini_agent_cog)
    discord_logger.info("Gemini bot is online")


@bot.event
async def on_message(message: discord.Message):
    user = message.author

    # ignore messages created by the bot, and if the bot is not mentioned in the chat
    if user == bot.user or not bot.user.mentioned_in(message=message):
        return

    prompt = None
    # if the message contains <@MEMBER_ID> (when the bot is mentioned), split at > and return the rest
    if message.content.startswith("<@"):
        prompt = message.content.split("> ")[1]
    else:  # otherwise it is a reply to a previous message, therefore will not include member Id
        prompt = message.content

    try:
        # send chat request to the agent and log the response
        content = gemini_agent.send_chat(user.name, prompt)
        discord_logger.info(
            "Chat request completed",
            extra=dict(username=user.name, prompt=prompt, response_length=len(content)),
        )
        # reply to the user with the content
        await message.reply(f"{content}")
    except Exception as e:
        content = str(e)
        discord_logger.error(
            "An exception occured when requesting for content.",
            extra=dict(exception=content),
        )
        await message.reply(f"There was an exception. {content}")


@bot.event
async def on_member_remove(member: discord.Member):
    if not member.bot:
        gemini_agent.remove_chat(member.name)
        discord_logger.info(
            f"Removed chat for member that left.", extra=dict(username=member.name)
        )


if __name__ == "__main__":
    bot.run(token=DISCORD_TOKEN)
