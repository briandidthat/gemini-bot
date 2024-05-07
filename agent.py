from datetime import datetime

from PIL import Image
from typing import Dict
from dataclasses import dataclass
from google.generativeai import GenerativeModel, ChatSession
from google.generativeai.types import ContentsType

from logger import chat_agent_logger, vision_agent_logger


@dataclass
class ChatInfo:
    """Dataclass to represent chat information for a user."""

    username: str
    chat: ChatSession
    creation_time: datetime
    last_message: datetime

    def serialize(self) -> Dict:
        return {
            "username": self.username,
            "creation_time": self.creation_time,
            "last_message": self.last_message,
            "history": len(self.chat.history),
        }


class ChatAgent:
    """Agent class to handle chat interactions with the generative model."""

    def __init__(self, model_name: str) -> None:
        self.__model: GenerativeModel = GenerativeModel(model_name)
        self.__request_count: int = 0
        self.__chats: Dict[str, ChatInfo] = dict()

    def set_model(self, model_name: str) -> None:
        self.__model = GenerativeModel(model_name)
        chat_agent_logger.info(
            "A new model has been set.", extra=dict(model_name=model_name)
        )

    def get_request_count(self) -> int:
        return self.__request_count

    def get_model_name(self) -> str:
        return self.__model.model_name

    def get_chat_for_user(self, username: str) -> ChatInfo | None:
        return self.__chats.get(username, None)

    def remove_chat(self, username: str) -> None:
        self.__chats.pop(username, None)
        chat_agent_logger.info(
            "Chat history has been deleted.", extra=dict(username=username)
        )

    def remove_all_chats(self) -> None:
        chats = len(self.__chats)
        self.__chats.clear()
        chat_agent_logger.info("All chats have been erased.", extra=dict(chats=chats))

    def send_chat(self, username: str, prompt: str) -> str:
        """Sends a chat interaction for a specific user.
        Args:
            username: The name of the user.
            prompt: The message to send within the chat.
        Returns:
            The text response generated by the chat model.
        """

        # Fetch existing chat data
        chat_info = self.get_chat_for_user(username)
        # If chat_info is None, then the user has no chat history, so we will create a new chat
        chat = None if not chat_info else chat_info.chat
        if chat is None:
            # Start a new chat if no chat history exists for the user
            chat = self.__model.start_chat(history=[])
            chat_info = ChatInfo(username, chat, datetime.now(), None)
            self.__chats[username] = chat_info
            chat_agent_logger.info(
                "New chat created", extra=dict(chat_info=chat_info.serialize())
            )

        response = chat.send_message(prompt)
        # set the last message time to now
        chat_info.last_message = datetime.now()
        return response.text


class VisionAgent:
    # class to handle vision interactions with the generative model
    def __init__(self, model_name: str):
        self.__model: GenerativeModel = GenerativeModel(model_name)

    def set_model(self, model_name: str) -> None:
        self.__model = GenerativeModel(model_name)
        vision_agent_logger.info(
            "A new model has been set.", extra=dict(model_name=model_name)
        )

    def get_model_name(self) -> str:
        return self.__model.model_name

    def analyze_image(self, username: str, image: Image.Image, prompt: str) -> str:
        """Generates content based on the prompt and image"""
        # generate the response using the image and text prompt
        response = self.__model.generate_content([image, prompt])
        vision_agent_logger.info(
            "Content generated using image and text prompt.",
            extra=dict(
                username=username,
                image_size=image.size,
                prompt=prompt,
                response_length=len(response),
            ),
        )
        return response


class Orchestrator:
    def __init__(
        self, chat_agent: ChatAgent, vision_agent: VisionAgent, daily_limit: int
    ):
        self.__chat_agent: ChatAgent = chat_agent
        self.__vision_agent: VisionAgent = vision_agent
        self.__daily_limit: int = daily_limit
        self.__request_count: int = 0

    def get_request_count(self) -> int:
        return self.__request_count

    def increase_request_count(self) -> None:
        self.__request_count += 1

    def send_chat(self, username: str, prompt: str) -> str:
        """Sends a chat interaction for a specific user."""

        self.__validate_request_limit()
        self.__validate_prompt(prompt)

        response = self.__chat_agent.send_chat(username, prompt)
        self.__request_count += 1
        return response

    def analyze_image(self, username: str, prompt: str, image: Image.Image) -> str:
        """Generates content based on the prompt and image"""
        self.__validate_request_limit()
        self.__validate_prompt(prompt)

        try:
            # open as image using PIL
            response = self.__vision_agent.analyze_image(username, image, prompt)
            self.__request_count += 1
            return response
        except Exception as e:
            vision_agent_logger.error(
                "Error while analyzing image.", extra=dict(error=str(e))
            )
            raise e

    def __validate_request_limit(self) -> None:
        """Will throw ValueError if the request limit will be exceeded."""
        less_than_limit = self.__request_count + 1 < self.__daily_limit
        if not less_than_limit:
            raise ValueError("Daily limit has been reached.")

    def __validate_prompt(self, prompt: str) -> None:
        """Will throw ValueError if the prompt is empty."""
        if not prompt:
            raise ValueError("Prompt is empty.")

        """Will throw ValueError if the prompt is greater than 1000 chars."""
        less_than_limit = len(prompt) < 1000
        if not less_than_limit:
            raise ValueError("Prompt is over 1k characters.")
