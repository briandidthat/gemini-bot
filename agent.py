import datetime

from typing import Dict
from dataclasses import dataclass
from logger import agent_logger
from discord.ext import commands, tasks
from google.generativeai import GenerativeModel, ChatSession


@dataclass
class ChatInfo:
    username: str
    chat: ChatSession
    creation_time: datetime.datetime


class Agent:
    def __init__(self, model_name: str, daily_limit: int) -> None:
        self.__model: GenerativeModel = GenerativeModel(model_name)
        self.__daily_limit: int = daily_limit
        self.__request_count: int = 0
        self.__chats: Dict[str, ChatInfo] = dict()

    def set_new_model(self, model_name: str) -> None:
        self.__model = GenerativeModel(model_name)

    def set_daily_limit(self, daily_limit: int) -> None:
        self.__daily_limit = daily_limit

    def get_request_count(self) -> int:
        return self.__request_count

    def get_model_name(self) -> str:
        return self.__model.model_name

    def reset_request_count(self) -> None:
        self.__request_count = 0

    def increase_request_count(self) -> None:
        self.__request_count += 1

    def remove_chat(self, username: str) -> None:
        self.__chats.pop(username, None)

    def send_chat(self, username: str, prompt: str) -> str:
        """Sends a chat interaction for a specific user.
        Args:
            username: The name of the user.
            prompt: The message to send within the chat.
        Returns:
            The text response generated by the chat model.
        """
        self.__validate_request_limit()
        self.__validate_prompt_limit(prompt)

        # Fetch existing chat data
        chat_info = self.__chats.get(username)
        chat = None if chat_info == None else chat_info.chat
        if chat_info == None:
            # Start a new chat if no chat history exists for the user
            chat = self.__model.start_chat(history=[])
            chat_info = ChatInfo(username, chat, datetime.datetime.now())
            self.__chats[username] = chat_info
            agent_logger.info("New chat created", extra=dict(chat_info=chat_info))

        response = chat.send_message(prompt)
        self.increase_request_count()
        return response.text

    def __validate_request_limit(self) -> None:
        """Will throw ValueError if the request limit will be exceeded."""
        less_than_limit = self.__request_count + 1 < self.__daily_limit
        if not less_than_limit:
            raise ValueError("Daily limit has been reached.")

    def __validate_prompt_limit(self, prompt: str) -> None:
        """Will throw ValueError if the prompt is greater than 1000 chars."""
        less_than_limit = len(prompt) < 1000
        if not less_than_limit:
            raise ValueError("Prompt is over 1k characters.")


# create time for scheduling task every day at 00:00:00
scheduled_time = datetime.time(hour=0, minute=0, second=0)


class AgentCog(commands.Cog, name="AgentCog"):
    """Cog implementation to run commands that are related to the Agent class"""

    def __init__(self, agent: Agent, chat_ttl: int):
        self.__agent: Agent = agent
        self.__chat_ttl: int = chat_ttl

    @tasks.loop(time=scheduled_time)
    async def reset_count_task(self):
        """This method resets the request count of the agent to 0 every day at 00:00:00 UTC"""
        agent_logger.info("Resetting request count to 0.")
        self.__agent.reset_request_count()

    @tasks.loop(time=scheduled_time)
    async def erase_chat_history(self):
        """This method erases the chat info of any chat that has exceeded the ttl (time to live)"""
        for username, chat_info in self.__agent.__chats.items():
            hours_elapsed = datetime.datetime.now() - chat_info.creation_time
            if hours_elapsed > self.__chat_ttl:
                agent_logger.info("Removing chat", extra=dict(username=username))
                self.__agent.remove_chat(username)
