from datetime import datetime, timedelta
from typing import Type
from PIL import Image

import discord
from discord.ext import commands, tasks

from agent import File, GeminiAgent
from exception import DiscordException, DoneForTheDayException
from logger import bot_logger


class Bot(commands.Bot):
    def __init__(
        self,
        agent: GeminiAgent,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.agent = agent

    """EVENTS"""

    async def on_ready(self) -> None:
        """Event handler for when the bot is ready."""
        bot_logger.info("Gemini bot is online")

    async def on_message(self, message: discord.Message) -> None:
        """Event handler for when a message is sent in the chat."""
        username = message.author.name

        # if the bot was mentioned in the message and the message was not created by the bot itself
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
                    attachments_length = len(message.attachments)
                    # if more than one message, reply to user letting them know only one file is accepted at a time
                    if attachments_length > 1:
                        await message.reply(
                            f"Only one file can be processed at a time."
                        )
                        bot_logger.error(
                            "Rejected file prompt due to file count.",
                            extra=dict(file_count=attachments_length),
                        )
                        return
                    # set the request type for logging
                    request_type = "vision"
                    # by this point there will only be one attachemnt, otherwise we would have responded to the user
                    attachment = message.attachments[0]
                    # process the file prompt and store the response as content
                    content = await self.process_file_prompt(
                        username, prompt, attachment
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
                        request_count=self.agent.request_count,
                    ),
                )
                # reply to the user with the content
                await message.reply(f"{content}")
            except DoneForTheDayException as e:
                bot_logger.error(
                    f"The request limit for today has been met.",
                    extra=dict(
                        exception=e.serialize(), username=username, prompt=prompt
                    ),
                )
                await message.reply(f"I am done for the day. Check back later.")
            except DiscordException as e:
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
            self.agent.remove_chat(member.name)
            bot_logger.info(
                f"Removed chat for member that left.", extra=dict(username=member.name)
            )

    """METHODS"""

    async def process_chat_prompt(
        self, username: str, prompt: str
    ) -> str | Type[DiscordException]:
        """Processes a chat prompt sent by a user."""
        try:
            response = self.agent.process_chat_prompt(username, prompt)
            return response
        except Exception as e:
            raise DiscordException(message=str(e), type=type(e).__name__)

    async def process_file_prompt(
        self, username: str, prompt: str, attachment: discord.Attachment
    ) -> str | Type[DiscordException]:
        """Processes an image and prompt sent by a user."""

        try:
            # if the attachment is null
            if not attachment:
                raise ValueError("No file attached.")

            attachment_file = await attachment.to_file()
            file = File(content=attachment_file, content_type=attachment.content_type)

            response = await self.agent.process_file_prompt(username, prompt, file)
            return response
        except Exception as e:
            raise DiscordException(message=str(e), type=type(e).__name__)


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

        self.bot.agent.remove_all_chats()
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
            self.bot.agent.set_model(model_name=content)
            await ctx.reply(f"New model set.")

    @tasks.loop(hours=2)
    async def erase_old_chats(self):
        """This method erases the chat info of any chat that has exceeded the ttl (time to live) of the last message"""
        today = datetime.now()

        for username, chat_info in self.bot.orchestrator.get_chats().items():
            if today - chat_info.last_message > self.chat_ttl:
                self.bot.agent.remove_chat(username)
