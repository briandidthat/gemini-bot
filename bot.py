import discord
from discord.ext import commands
from agent import Agent
from logger import bot_logger


class Bot(commands.Bot):
    def __init__(self, gemini_agent: Agent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gemini_agent = gemini_agent

    async def on_ready(self):
        """Event handler for when the bot is ready."""
        bot_logger.info("Gemini bot is online")

    async def on_message(self, message: discord.Message):
        """Event handler for when a message is sent in the chat."""
        user = message.author

        # ignore messages created by the bot, and if the bot is not mentioned in the chat
        if user == self.user or not self.user.mentioned_in(message=message):
            return

        prompt = None
        # if the message contains <@MEMBER_ID> (when the bot is mentioned), split at > and return the rest
        if message.content.startswith("<@"):
            prompt = message.content.split("> ")[1]
        else:  # otherwise it is a reply to a previous message, therefore will not include member Id
            prompt = message.content

        try:
            # send chat request to the agent and log the response
            content = self.gemini_agent.send_chat(user.name, prompt)
            bot_logger.info(
                "Chat request completed",
                extra=dict(
                    username=user.name, prompt=prompt, response_length=len(content)
                ),
            )
            # reply to the user with the content
            await message.reply(f"{content}")
        except Exception as e:
            content = str(e)
            bot_logger.error(
                "An exception occured when requesting for content.",
                extra=dict(exception=content),
            )
            await message.reply(f"There was an exception. {content}")

    async def on_member_remove(self, member: discord.Member):
        """Event handler for when a member leaves the server."""
        if not member.bot:
            self.gemini_agent.remove_chat(member.name)
            bot_logger.info(
                f"Removed chat for member that left.", extra=dict(username=member.name)
            )
