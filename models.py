from dataclasses import dataclass
import datetime
from typing import IO, Dict

from google.generativeai import ChatSession


@dataclass
class File:
    content: IO
    content_type: str


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
