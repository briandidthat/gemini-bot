from datetime import datetime
from typing import Type

import discord
from discord.ext import commands, tasks

from agent import GeminiAgent
from exception import DiscordException, DoneForTheDayException
from logger import bot_logger
from utils import get_file, get_time_delta


class Bot(commands.Bot):
    def __init__(
        self,
        owner: str,
        agent: GeminiAgent,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.__owner = owner
        self.__agent = agent

    """EVENTS"""

    async def on_ready(self) -> None:
        """Event handler for when the bot is ready."""
        bot_logger.info("Gemini bot is online")

    async def on_message(self, message: discord.Message) -> None:
        """
        Event handler for when a message is sent in the chat.

        This function processes messages sent in the chat and performs actions based on whether the bot is mentioned.
        If the bot is mentioned, it processes the message content or attachments and replies with the appropriate response.
        If the bot is not mentioned, it continues processing commands as expected by the framework.

        Args:
            message (discord.Message): The message object that was sent in the chat.

        Returns:
            None

        Raises:
            DoneForTheDayException: If the request limit for the day has been met.
            DiscordException: If an exception occurs when making a request to the GeminiAPI.
        """
        """Event handler for when a message is sent in the chat."""
        username = message.author.name

        # if the bot was mentioned in the message and the message was not created by the bot itself
        if self.user.mentioned_in(message) and username != self.user.name:

            prompt, content, request_type = None, None, None

            # if the message contains <@MEMBER_ID> (when the bot is mentioned), split at > and return the rest
            if message.content.startswith("<@"):
                message_array = message.content.split("> ")
                # if the message array is less than or equal to 1, no prompt was provided
                if len(message_array) <= 1:
                    await message.reply("No prompt was provided.")
                    return

                prompt = message_array[1]
            else:  # otherwise it is a reply to a previous message, therefore will not include member Id
                prompt = message.content

            # ensure that there is at minimum 1 character in the prompt (to avoid wasting tokens)
            if not prompt or len(prompt) < 1:
                # reply to the user with the error message
                await message.reply("Invalid prompt")
                return

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
                            "Only one file can be processed at a time.",
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
                    content = await self.process_chat_prompt(username, prompt)

                end_time = datetime.now()
                # calculate runtime in milliseconds
                runtime = int((end_time.timestamp() - start_time.timestamp()) * 1000)

                bot_logger.info(
                    "Processed content request.",
                    extra=dict(
                        requestType=request_type,
                        username=username,
                        runtime=runtime,
                        requestCount=self.agent.request_count,
                    ),
                )
                # reply to the user with the content
                await message.reply(f"{content}")
            # handle exceptions for exceeding GeminiAPI request limit
            except DoneForTheDayException as e:
                bot_logger.error(
                    f"The request limit for today has been met.",
                    extra=dict(
                        exception=e.serialize(), username=username, prompt=prompt
                    ),
                )
                await message.reply(f"I am done for the day. Check back later.")
            # handle exceptions for exceeding GeminiAPI request limit
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

    @property
    def owner(self) -> str:
        return self.__owner

    @owner.setter
    def set_owner(self, owner: str):
        self.__owner = owner

    @property
    def agent(self) -> GeminiAgent:
        return self.__agent

    async def process_chat_prompt(
        self, username: str, prompt: str
    ) -> str | Type[DiscordException]:
        """Processes a chat prompt sent by a user."""
        try:
            response = await self.agent.process_chat_prompt(username, prompt)
            return response
        except Exception as e:
            raise DiscordException(message=str(e), type=type(e).__name__)

    async def process_file_prompt(
        self, username: str, prompt: str, attachment: discord.Attachment
    ) -> str | Type[DiscordException]:
        """Processes an image and prompt sent by a user."""

        try:
            attachment_file = await attachment.to_file()
            file = get_file(
                attachment.filename, attachment_file, attachment.content_type
            )

            response = await self.agent.process_file_prompt(username, prompt, file)
            # close the file since we have gotten a response from gemini API
            file.close()
            return response
        except Exception as e:
            raise DiscordException(message=str(e), type=type(e).__name__)


class BotCog(commands.Cog, name="BotCog"):
    """Cog implementation to run commands that are related to the Bot class. Will also run a background task to erase old chats."""

    def __init__(self, bot: Bot, chat_ttl: int):
        self.bot = bot
        self.chat_ttl = chat_ttl

    def is_owner(self, ctx: commands.Context):
        return ctx.author.name == self.bot.owner

    @commands.command(name="set-owner", help="Set the owner of the bot.")
    async def set_owner(self, ctx: commands.Context):
        """Command to set the owner of the bot."""
        if not self.is_owner(ctx):
            return
        
        user = ctx.author.name
        self.bot.set_owner(user)

    # add command to erase all chats manually. will only be accepted by the bot owner
    @commands.command(name="erase_chats", help="Erase all chats from the chat agent.")
    async def erase_chats(self, ctx: commands.Context):
        if not self.is_owner(ctx):
            return

        self.bot.agent.remove_all_chats()
        await ctx.reply("All chats have been erased.")

    # add command to set a new generative model for the agent
    @commands.command(name="set_model", help="Set a new model for the gemini agent.")
    async def set_chat_model(self, ctx: commands.Context):
        """Command to set a new generative model for the gemini agent."""
        if not self.is_owner(ctx):
            return

        content = ctx.message.content
        if content:
            self.bot.agent.set_model(model_name=content)
            await ctx.reply(f"New model set.")

    @commands.command(
        name="add_model", help="Add a new model to the accepted models list."
    )
    async def add_model(self, ctx: commands.Context):
        """Command to add a new model to the accepted models list."""
        if not self.is_owner(ctx):
            return

        content = ctx.message.content
        if content:
            self.bot.agent.add_model()

    @tasks.loop(hours=2)
    async def erase_old_chats(self):
        """This method erases the chat of any chat that has exceeded the ttl (time to live) of the last message"""

        for username, chat in self.bot.agent.chats.items():
            duration = get_time_delta(chat.last_message, datetime.now())
            if duration > self.chat_ttl:
                self.bot.agent.remove_chat(username)
