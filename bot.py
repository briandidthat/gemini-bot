from datetime import datetime

import discord
from discord.ext import commands

from agent import Agent
from logger import bot_logger


class Bot(commands.Bot):
    def __init__(self, gemini_agent: Agent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gemini_agent = gemini_agent

    """EVENTS"""

    async def on_ready(self):
        """Event handler for when the bot is ready."""
        bot_logger.info("Gemini bot is online")

    async def on_message(self, message: discord.Message):
        """Event handler for when a message is sent in the chat."""
        username = message.author.name

        # if the bot was mentioned in the message and the message was not created by the bot
        if self.user.mentioned_in(message) and username != self.user.name:

            prompt = None
            # if the message contains <@MEMBER_ID> (when the bot is mentioned), split at > and return the rest
            if message.content.startswith("<@"):
                prompt = message.content.split("> ")[1]
            else:  # otherwise it is a reply to a previous message, therefore will not include member Id
                prompt = message.content

            try:
                start_time = datetime.now()
                # send chat request to the agent and log the response
                content = self.gemini_agent.send_chat(username, prompt)
                end_time = datetime.now()
                runtime = int((end_time.timestamp() - start_time.timestamp()) * 1000)

                bot_logger.info(
                    "Chat request completed",
                    extra=dict(
                        username=username,
                        prompt=prompt,
                        response_length=len(content),
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
            self.gemini_agent.remove_chat(member.name)
            bot_logger.info(
                f"Removed chat for member that left.", extra=dict(username=member.name)
            )


class BotCog(commands.Cog, name="BotCog"):
    def __init__(self, bot: Bot, bot_owner: str):
        self.bot = bot
        self.bot_owner = bot_owner

    # add command to erase all chats manually. will only be accepted by the bot owner
    @commands.command(name="erase_chats", help="Erase all chats from the agent.")
    async def erase_chats(self, ctx: commands.Context):
        if ctx.author.name != self.bot_owner:
            return

        self.bot.gemini_agent.remove_all_chats()
        await ctx.reply("All chats have been erased.")

    # add command to set a new generative model for the agent
    @commands.command(name="set_new_model", help="Set a new model for the agent.")
    async def set_new_model(self, ctx: commands.Context):
        user = ctx.author.name
        if user != self.bot_owner:
            return

        content = ctx.message.content
        if content:
            try:
                self.bot.gemini_agent.set_model(model_name=content)
                await ctx.reply(f"New model set.")
            except Exception as e:
                await ctx.reply(f"An error occured: {str(e)}")
