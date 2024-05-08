from datetime import datetime, timedelta
from typing import List

import discord
from discord.ext import commands, tasks
from PIL import Image

from agent import ChatAgent, VisionAgent, Orchestrator
from logger import bot_logger


class Bot(commands.Bot):
    def __init__(
        self,
        chat_agent: ChatAgent,
        vision_agent: VisionAgent,
        daily_limit: int,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.orchestrator = Orchestrator(chat_agent, vision_agent, daily_limit)

    """EVENTS"""

    async def on_ready(self):
        """Event handler for when the bot is ready."""
        bot_logger.info("Gemini bot is online")

    async def on_message(self, message: discord.Message):
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
                # if the message has attachments, process the image prompt via the vision agent
                if message.attachments:
                    request_type = "vision"
                    content = await self.process_image_prompt(
                        username, prompt, message.attachments
                    )
                else:
                    # else send chat request to the chat agent and log the response
                    request_type = "chat"
                    content = self.orchestrator.send_chat(username, prompt)

                end_time = datetime.now()
                # calculate runtime in milliseconds
                runtime = int((end_time.timestamp() - start_time.timestamp()) * 1000)

                bot_logger.info(
                    "Processed content request.",
                    extra=dict(
                        request_type=request_type,
                        username=username,
                        prompt=prompt,
                        runtime=runtime,
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
        else:
            # since the bot was not mentioned, continue processing as expected by the framework
            await self.process_commands(message)

    async def on_member_remove(self, member: discord.Member):
        """Event handler for when a member leaves the server."""
        if not member.bot:
            self.orchestrator.__chat_agent.remove_chat(member.name)
            bot_logger.info(
                f"Removed chat for member that left.", extra=dict(username=member.name)
            )

    """METHODS"""

    async def process_image_prompt(
        self, username: str, prompt: str, attachments: List[discord.Attachment]
    ):
        """Processes an image and prompt sent by a user."""

        # if no attachments or empty list, return
        if not attachments or len(attachments) == 0:
            raise ValueError("No image attached.")

        # there should only be one element
        attachment = attachments[0]

        try:
            # convert the attachment to a file
            file = await attachment.to_file()
            type(file)
            # open as image using PIL
            image = Image.open(fp=file.fp)
            # generate the response using the image and text prompt
            response = self.orchestrator.analyze_image(username, prompt, image)
            return response
        except Exception as e:
            raise e


class BotCog(commands.Cog, name="BotCog"):
    """Cog implementation to run commands that are related to the Bot class."""

    def __init__(self, bot: Bot, bot_owner: str):
        self.bot = bot
        self.bot_owner = bot_owner

    # add command to erase all chats manually. will only be accepted by the bot owner
    @commands.command(name="erase_chats", help="Erase all chats from the agent.")
    async def erase_chats(self, ctx: commands.Context):
        if ctx.author.name != self.bot_owner:
            return

        self.bot.orchestrator.__chat_agent.remove_all_chats()
        await ctx.reply("All chats have been erased.")

    # add command to set a new generative model for the agent
    @commands.command(name="set_new_chat_model", help="Set a new model for the agent.")
    async def set_new_chat_model(self, ctx: commands.Context):
        user = ctx.author.name
        if user != self.bot_owner:
            return

        content = ctx.message.content
        if content:
            try:
                self.bot.orchestrator.set_chat_model(model_name=content)
                await ctx.reply(f"New model set.")
            except Exception as e:
                await ctx.reply(f"An error occured: {str(e)}")

    # add command to set a new generative model for the vision agent
    @commands.command(name="set_vision_model", help="Set a new model for the agent.")
    async def set_new_chat_model(self, ctx: commands.Context):
        user = ctx.author.name
        if user != self.bot_owner:
            return

        content = ctx.message.content
        if content:
            try:
                self.bot.orchestrator.set_vision_model(model_name=content)
                await ctx.reply(f"New model set.")
            except Exception as e:
                await ctx.reply(f"An error occured: {str(e)}")


class ChatAgentCog(commands.Cog, name="AgentCog"):
    """Cog implementation to run commands that are related to the Agent class"""

    def __init__(self, agent: ChatAgent, chat_ttl: timedelta):
        self.__agent: ChatAgent = agent
        self.__chat_ttl: timedelta = chat_ttl

    @tasks.loop(hours=24)
    async def reset_count_task(self):
        """This method resets the request count of the agent to 0 every 24 hours"""
        self.__agent.reset_request_count()

    @tasks.loop(hours=6)
    async def erase_old_chats(self):
        """This method erases the chat info of any chat that has exceeded the ttl (time to live) of the last message"""
        today = datetime.now()

        for username, chat_info in self.__agent.__chats.items():
            if today - chat_info.last_message > self.__chat_ttl:
                self.__agent.remove_chat(username)
