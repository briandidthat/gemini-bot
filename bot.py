from datetime import datetime, timedelta
from typing import Dict, List, Type

import discord
from discord.ext import commands, tasks
from PIL import Image

from agent import GeminiAgent, Orchestrator
from logger import bot_logger


class BotException(Exception):
    """Custom exception class for the discord bot."""

    def __init__(self, message: str, type: str):
        super().__init__(message)
        self.message = message
        self.type = type

    def serialize(self) -> Dict[str, str]:
        return dict(message=self.message, type=self.type)


class Bot(commands.Bot):
    def __init__(
        self,
        gemini_agent: GeminiAgent,
        daily_limit: int,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.orchestrator: Orchestrator = Orchestrator(gemini_agent, daily_limit)

    """EVENTS"""

    async def on_ready(self) -> None:
        """Event handler for when the bot is ready."""
        bot_logger.info("Gemini bot is online")

    async def on_message(self, message: discord.Message) -> None:
        """Event handler for when a message is sent in the chat."""
        username = message.author.name

        # if the bot was mentioned in the message and the message was not created by the bot
        if self.user.mentioned_in(message) and username != self.user.name:

            prompt, content, request_type = None, None, None

            # if the message contains <@MEMBER_ID> (when the bot is mentioned), split at > and return the rest
            if message.content.startswith("<@"):
                prompt = message.content.split("> ")[1]
            else:  # otherwise it is a reply to a previous message, therefore will not include member Id
                prompt = message.content

            try:
                start_time = datetime.now()
                # if the message has attachments, process the image prompt via the vision agent. Will throw exception if not an image
                if message.attachments:
                    request_type = "vision"
                    content = await self.process_image_prompt(
                        username, prompt, message.attachments
                    )
                else:
                    # else send chat request to the chat agent and log the response
                    request_type = "chat"
                    content = self.process_chat_prompt(username, prompt)

                end_time = datetime.now()
                # calculate runtime in milliseconds
                runtime = int((end_time.timestamp() - start_time.timestamp()) * 1000)

                bot_logger.info(
                    "Processed content request.",
                    extra=dict(
                        request_type=request_type,
                        username=username,
                        runtime=runtime,
                        request_count=self.orchestrator.get_request_count(),
                    ),
                )
                # reply to the user with the content
                await message.reply(f"{content}")
            except BotException as e:
                bot_logger.error(
                    f"An exception occured when making a {request_type} request.",
                    extra=dict(
                        exception=e.serialize(), username=username, prompt=prompt
                    ),
                )
                await message.reply(f"{e.message}")
        else:
            # since the bot was not mentioned, continue processing as expected by the framework
            await self.process_commands(message)

    async def on_member_remove(self, member: discord.Member):
        """Event handler for when a member leaves the server."""
        if not member.bot:
            self.orchestrator.__gemini_agent.remove_chat(member.name)
            bot_logger.info(
                f"Removed chat for member that left.", extra=dict(username=member.name)
            )

    """METHODS"""

    async def process_chat_prompt(
        self, username: str, prompt: str
    ) -> str | Type[BotException]:
        """Processes a chat prompt sent by a user."""
        try:
            response = self.orchestrator.process_chat_prompt(username, prompt)
            return response
        except Exception as e:
            raise BotException(message=str(e), type=type(e).__name__)

    async def process_image_prompt(
        self, username: str, prompt: str, attachments: List[discord.Attachment]
    ) -> str | Type[BotException]:
        """Processes an image and prompt sent by a user."""

        try:
            # if no attachments or empty list, return
            if not attachments or len(attachments) == 0:
                raise ValueError("No image attached.")

            # there should only be one element
            attachment = attachments[0]

            file = await attachment.to_file()
            # open as image using PIL
            image = Image.open(fp=file.fp)
            # generate the response using the image and text prompt
            response = self.orchestrator.process_image_prompt(username, prompt, image)
            return response
        except Exception as e:
            raise BotException(message=str(e), type=type(e).__name__)


class BotCog(commands.Cog, name="BotCog"):
    """Cog implementation to run commands that are related to the Bot class. Will also run a background task to erase old chats."""

    def __init__(self, bot: Bot, bot_owner: str, chat_ttl: timedelta):
        self.bot = bot
        self.bot_owner = bot_owner
        self.chat_ttl = chat_ttl

    # add command to erase all chats manually. will only be accepted by the bot owner
    @commands.command(name="erase_chats", help="Erase all chats from the chat agent.")
    async def erase_chats(self, ctx: commands.Context):
        if ctx.author.name != self.bot_owner:
            return

        self.bot.orchestrator.remove_all_chats()
        await ctx.reply("All chats have been erased.")

    # add command to set a new generative model for the agent
    @commands.command(name="set_model", help="Set a new model for the gemini agent.")
    async def set_chat_model(self, ctx: commands.Context):
        """Command to set a new generative model for the gemini agent."""
        user = ctx.author.name
        if user != self.bot_owner:
            return

        content = ctx.message.content
        if content:
            self.bot.orchestrator.set_chat_model(model_name=content)
            await ctx.reply(f"New model set.")


    @tasks.loop(hours=6)
    async def erase_old_chats(self):
        """This method erases the chat info of any chat that has exceeded the ttl (time to live) of the last message"""
        today = datetime.now()

        for username, chat_info in self.bot.orchestrator.get_chats().items():
            if today - chat_info.last_message > self.chat_ttl:
                self.bot.orchestrator.remove_chat(username)
