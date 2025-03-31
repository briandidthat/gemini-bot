from datetime import datetime
from typing import Dict
from google import genai

from exception import DoneForTheDayException
from logger import gemini_agent_logger
from models import Chat, File


class GeminiAgent:
    """
    Agent responsible for managing chat interactions with a multimodal model.

    Parameters:
    api_key (str): The api key for google generative AI. (https://developers.google.com/generative-ai/docs/get-started)
    model_name (str): The name of the generative model to use.
    daily_limit (int): The maximum number of requests allowed per day.

    Attributes:
            client (genai.Client): The client used to make requests to Google GenAI.
            chats (Dict[str, Chat]): A dictionary storing chat sessions for users.
            request_count (int): The current count of requests made.

    Methods:
            get_chat_for_user(username: str) -> Chat | None: Retrieves the chat session for a specific user.
            set_model(model_name: str): Sets a new generative model.
            store_chat(chat: Chat): Stores a chat session.
            process_chat_prompt(username: str, prompt: str) -> str: Sends a chat interaction for a specific user.
            process_file_prompt(username: str, prompt: str, file: File) -> str: Sends a chat interaction with a file for a specific user.
    """

    def __init__(self, api_key: str, model_name: str, daily_limit: int) -> None:
        self.__client: genai.Client = genai.Client(api_key=api_key)
        self.__model: str = model_name
        self.__daily_limit: int = daily_limit
        self.__chats: Dict[str, Chat] = dict()
        self.__request_count: int = 0

    """ Properties """

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

    """ Private Methods """

    def __increment_request_count(self) -> None:
        self.__request_count += 1

    # def __upload_file(self, file_name: str, content_type: str):
    #     file = genai.upload_file(path=file_name)
    #     return File(file_name, file, content_type)

    # def __delete_file(file_name: str) -> None:
    #     genai.delete_file(file_name)

    def __validate_request_limit(self) -> None:
        """Will throw DoneForTheDayException if the request limit will be exceeded."""
        less_than_limit = self.request_count + 1 <= self.daily_limit
        if not less_than_limit:
            raise DoneForTheDayException(
                message="Daily limit has been reached.", type=type(ValueError).__name__
            )

    """ Public Methods """

    def get_chat_for_user(self, username: str) -> Chat | None:
        return self.chats.get(username, None)

    def set_model(self, model_name: str) -> None:
        self.__client = model_name
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
        chats = len(self.chats)
        self.chats.clear()
        gemini_agent_logger.info(
            "All chats have been erased.", extra=dict(chats_deleted=chats)
        )

    async def generate_content(self, prompt: str) -> str:
        """Generates content using the multimodal model.\n
        Args:
            prompt: The message to send within the chat.
        Returns:
            The text response generated by the chat model.
        """
        self.__validate_request_limit()

        content = self.__client.models.generate_content(
            model=self.__model, prompt=prompt
        )
        return content.text

    async def process_chat_prompt(self, username: str, prompt: str) -> str:
        """Sends a chat interaction for a specific user.\n
        Args:
            username: The name of the user.
            prompt: The message to send within the chat.
        Returns:
            The text response generated by the chat model.
        """
        self.__validate_request_limit()

        # Fetch existing chat data
        chat = self.get_chat_for_user(username)
        # If chat is None, then the user has no chat history, so we will create a new chat
        if chat is None:
            # Start a new chat if no chat history exists for the user
            chat = self.__client.start_chat(history=[])
            chat = Chat(username, chat, datetime.now(), None)
            self.store_chat(chat)

        response = await chat.session.send_message_async(prompt)
        # set the last message time to now
        chat.last_message = datetime.now()
        # log the chat message sent
        gemini_agent_logger.info(
            "Chat message sent.",
            extra=dict(username=username, prompt=prompt, chat=chat.serialize()),
        )
        # increment request count
        self.__increment_request_count()
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
        self.__validate_request_limit()

        # generate the response using the file and text prompt
        response = await self.__client.generate_content_async([file.content, prompt])
        # close the file since we dont need it any more
        file.close()
        gemini_agent_logger.info(
            "Content generated using file and text prompt.",
            extra=dict(
                username=username,
                prompt=prompt,
                filename=file.name,
                responseLength=len(response.text),
            ),
        )
        return response.text
