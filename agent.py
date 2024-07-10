from datetime import datetime
from typing import Dict

import google.generativeai as genai

from logger import gemini_agent_logger
from models import Chat, File
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
        self.__chats: Dict[str, Chat] = dict()
        self.__daily_limit: int = daily_limit
        self.__request_count: int = 0

    """ Properties """

    @property
    def model(self) -> genai.GenerativeModel:
        return self.__model

    @model.setter
    def model(self, model_name):
        self.set_model(model_name)

    @property
    def chats(self) -> Dict[str, Chat]:
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

    def get_chat_for_user(self, username: str) -> Chat | None:
        return self.__chats.get(username, None)

    def set_model(self, model_name: str) -> None:
        self.__model = genai.GenerativeModel(model_name)
        gemini_agent_logger.info(
            "A new model has been set.", extra=dict(model_name=model_name)
        )

    def store_chat(self, chat: Chat):
        if chat:
            self.chats[chat.username] = chat
            gemini_agent_logger.info(
                "A new chat has been stored.", extra=chat.serialize()
            )

    def remove_chat(self, username: str) -> None:
        chat = self.__chats.pop(username, None)
        if chat:
            gemini_agent_logger.info(
                "Chat history has been deleted.",
                extra=dict(chat_info=chat.serialize()),
            )

    def remove_all_chats(self) -> None:
        chats = len(self.__chats)
        self.__chats.clear()
        gemini_agent_logger.info(
            "All chats have been erased.", extra=dict(chats_deleted=chats)
        )

    async def process_chat_prompt(self, username: str, prompt: str) -> str:
        """Sends a chat interaction for a specific user.\n
        Args:
            username: The name of the user.
            prompt: The message to send within the chat.
        Returns:
            The text response generated by the chat model.
        """
        validate_request_limit(self.daily_limit, self.request_count)

        # Fetch existing chat data
        chat = self.get_chat_for_user(username)
        # If chat is None, then the user has no chat history, so we will create a new chat
        if chat is None:
            # Start a new chat if no chat history exists for the user
            chat = self.model.start_chat(history=[])
            chat = Chat(username, chat, datetime.now(), None)
            self.store_chat(chat)

        response = chat.session.send_message(prompt)
        # set the last message time to now
        chat.last_message = datetime.now()
        # log the chat message sent
        gemini_agent_logger.info(
            "Chat message sent.",
            extra=dict(username=username, prompt=prompt, chat_info=chat.serialize()),
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
        validate_request_limit(self.daily_limit, self.request_count)

        # generate the response using the file and text prompt
        response = self.__model.generate_content([file.content, prompt])
        # close the file since we dont need it any more
        file.close()
        gemini_agent_logger.info(
            "Content generated using image and text prompt.",
            extra=dict(
                username=username,
                prompt=prompt,
                response_length=len(response.text),
            ),
        )
        return response.text

    def upload_file(self, file_name: str, content_type: str):
        file = genai.upload_file(path=file_name)
        return File(file_name, file, content_type)

    def delete_file(file_name: str) -> None:
        genai.delete_file(file_name)
