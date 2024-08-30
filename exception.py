from typing import Dict


class BaseException(Exception):
    def __init__(self, message: str, type: str):
        self.message = message
        self.type = type
        super().__init__(message)

    def serialize(self) -> Dict[str, str]:
        return dict(message=self.message, type=self.type)


class DiscordException(BaseException):
    """Custom exception class for the discord bot."""

    pass


class GeminiException(BaseException):
    """Custom exception class for the gemini agent."""

    pass


class FileProcessingException(BaseException):
    """Custom exception for when the file is unable to be processed"""
    pass


class DoneForTheDayException(BaseException):
    """Custom Exception for when the GeminiAPI request limit has been exceeded"""

    pass
