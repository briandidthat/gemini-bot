from datetime import datetime

from typing import Dict, IO
from dataclasses import dataclass

import google.generativeai as genai

from logger import gemini_agent_logger
from models import ChatInfo, File
from utils import validate_request_limit


class GeminiAgent:
    """Agent class to handle chat interactions with the generative model.\n
    The model must be multimodal in order to handle all requests.\n
    Params:
        - model_name: str
        - daily_limit: int
    """

    def __init__(self, model_name: str, daily_limit) -> None:
        self.__model: genai.GenerativeModel = genai.GenerativeModel(model_name)
        self.__chats: Dict[str, ChatInfo] = dict()
        self.__daily_limit: int = daily_limit
        self.__request_count: int = 0

    """ Properties """

    @property
    def model(self) -> str:
        return self.__model.model_name

    @model.setter
    def model(self, model_name):
        self.set_model(model_name)

    @property
    def chats(self) -> Dict[str, ChatInfo]:
        return self.__chats

    @property
    def daily_limit(self) -> int:
        return self.__daily_limit

    @daily_limit.setter
    def daily_limit(self, daily_limit):
        self.__daily_limit = daily_limit

    @property
    def request_count(self) -> int:
        return self.__request_count

    """ Methods """

    def increment_request_count(self) -> None:
        self.__request_count += 1

    def get_chat_for_user(self, username: str) -> ChatInfo | None:
        return self.__chats.get(username, None)

    def set_model(self, model_name: str) -> None:
        self.__model = genai.GenerativeModel(model_name)
        gemini_agent_logger.info(
            "A new model has been set.", extra=dict(model_name=model_name)
        )

    def remove_chat(self, username: str) -> None:
        chat_info = self.__chats.pop(username, None)
        if chat_info is not None:
            gemini_agent_logger.info(
                "Chat history has been deleted.",
                extra=dict(chat_info=chat_info.serialize()),
            )

    def remove_all_chats(self) -> None:
        chats = len(self.__chats)
        self.__chats.clear()
        gemini_agent_logger.info(
            "All chats have been erased.", extra=dict(chats_deleted=chats)
        )

    def process_chat_prompt(self, username: str, prompt: str) -> str:
        """Sends a chat interaction for a specific user.\n
        Args:
            username: The name of the user.
            prompt: The message to send within the chat.
        Returns:
            The text response generated by the chat model.
        """
        validate_request_limit(self.__daily_limit, self.__request_count)

        # Fetch existing chat data
        chat_info = self.get_chat_for_user(username)
        # If chat_info is None, then the user has no chat history, so we will create a new chat
        chat = None if not chat_info else chat_info.chat
        if chat is None:
            # Start a new chat if no chat history exists for the user
            chat = self.__model.start_chat(history=[])
            chat_info = ChatInfo(username, chat, datetime.now(), None)
            self.__chats[username] = chat_info

        response = chat.send_message(prompt)
        # set the last message time to now
        chat_info.last_message = datetime.now()
        # log the chat message sent
        gemini_agent_logger.info(
            "Chat message sent.",
            extra=dict(
                username=username, prompt=prompt, chat_info=chat_info.serialize()
            ),
        )
        # increment request count
        self.increment_request_count()
        return response.text

    async def process_file_prompt(
        self,
        username: str,
        prompt: str,
        file: File,
    ) -> str:
        """Sends a chat interaction for a specific user.\n
        Args:
            username: The name of the user.
            prompt: The message to send within the chat.
            file: The file to be processed by the model.
        Returns:
            The text response generated by the chat model.
        """
        validate_request_limit(self.__daily_limit, self.__request_count)

        # generate the response using the file and text prompt
        response = self.__model.generate_content([file.content, prompt])
        # close the file since we dont need it any more
        file.content.close()
        gemini_agent_logger.info(
            "Content generated using image and text prompt.",
            extra=dict(
                username=username,
                prompt=prompt,
                response_length=len(response.text),
            ),
        )
        return response.text
