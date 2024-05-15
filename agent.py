from datetime import datetime

from PIL import Image
from typing import Dict
from dataclasses import dataclass
from google.generativeai import GenerativeModel, ChatSession

from logger import gemini_agent_logger


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


class GeminiAgent:
    """Agent class to handle chat interactions with the generative model. The model must be multimodal in order to handle all requests."""

    def __init__(self, model_name: str) -> None:
        self.__model: GenerativeModel = GenerativeModel(model_name)
        self.__request_count: int = 0
        self.__chats: Dict[str, ChatInfo] = dict()

    def set_model(self, model_name: str) -> None:
        self.__model = GenerativeModel(model_name)
        gemini_agent_logger.info(
            "A new model has been set.", extra=dict(model_name=model_name)
        )

    def get_request_count(self) -> int:
        return self.__request_count

    def get_model_name(self) -> str:
        return self.__model.model_name

    def get_chat_for_user(self, username: str) -> ChatInfo | None:
        return self.__chats.get(username, None)

    def get_chats(self) -> Dict[str, ChatInfo]:
        return self.__chats

    def remove_chat(self, username: str) -> None:
        self.__chats.pop(username, None)
        gemini_agent_logger.info(
            "Chat history has been deleted.", extra=dict(username=username)
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
        return response.text

    def process_image_prompt(
        self,
        username: str,
        prompt: str,
        image: Image.Image,
    ) -> str:
        """Sends a chat interaction for a specific user.\n
        Args:
            username: The name of the user.
            image: The image to be processed by the vision model.
            prompt: The message to send within the chat.
        Returns:
            The text response generated by the chat model.
        """

        # generate the response using the image and text prompt
        response = self.__model.generate_content([image, prompt])
        gemini_agent_logger.info(
            "Content generated using image and text prompt.",
            extra=dict(
                username=username,
                image_size=image.size,
                prompt=prompt,
                response_length=len(response.text),
            ),
        )
        return response.text


class Orchestrator:
    def __init__(self, gemini_agent: GeminiAgent, daily_limit: int):
        self.__gemini_agent: GeminiAgent = gemini_agent
        self.__daily_limit: int = daily_limit
        self.__request_count: int = 0

    def get_request_count(self) -> int:
        return self.__request_count

    def get_chats(self) -> Dict[str, ChatInfo]:
        return self.__gemini_agent.get_chats()

    def set_model(self, model_name: str) -> None:
        self.__gemini_agent.set_model(model_name)

    def increase_request_count(self) -> None:
        self.__request_count += 1

    def remove_chat(self, username: str) -> None:
        self.__gemini_agent.remove_chat(username)

    def remove_all_chats(self) -> None:
        self.__gemini_agent.remove_all_chats()

    def process_chat_prompt(self, username: str, prompt: str) -> str:
        """Sends a chat interaction for a specific user."""

        self.__validate_request_limit()
        self.__validate_prompt(prompt)

        response = self.__gemini_agent.process_chat_prompt(username, prompt)
        self.__request_count += 1
        return response

    def process_image_prompt(
        self, username: str, prompt: str, image: Image.Image
    ) -> str:
        """Generates content based on the prompt and image"""
        self.__validate_request_limit()
        self.__validate_prompt(prompt)

        response = self.__gemini_agent.process_image_prompt(username, prompt, image)
        self.__request_count += 1
        return response

    def __validate_request_limit(self) -> None:
        """Will throw ValueError if the request limit will be exceeded."""
        less_than_limit = self.__request_count + 1 < self.__daily_limit
        if not less_than_limit:
            raise ValueError("Daily limit has been reached.")

    def __validate_prompt(self, prompt: str) -> None:
        """Will throw ValueError if the prompt is empty or greater than 1000 chars."""
        if not prompt:
            raise ValueError("Prompt is empty.")

        """Will throw ValueError if the prompt is greater than 1000 chars."""
        less_than_limit = len(prompt) < 1000
        if not less_than_limit:
            raise ValueError("Prompt is over 1k characters.")
