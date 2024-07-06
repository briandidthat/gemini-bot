import datetime
from dataclasses import dataclass
from typing import IO, Dict

from google.generativeai import ChatSession


@dataclass
class File:
    name: str
    content: IO
    content_type: str

    def serialize(self):
        return {"name": self.name, "content_type": self.content_type}

    def close(self):
        self.content.close()


@dataclass
class Chat:
    """Dataclass to represent chat information for a user."""

    username: str
    session: ChatSession
    creation_time: datetime
    last_message: datetime

    def serialize(self) -> Dict:
        return {
            "username": self.username,
            "creation_time": self.creation_time,
            "last_message": self.last_message,
            "history": len(self.session.history),
        }
