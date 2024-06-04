from typing import Dict

from discord import Attachment


ALLOWED_FILE_TYPES: Dict[str, bool] = {
    "application/pdf": True,
    "text/plain; charset=utf-8": True,
    "image/jpeg": True,
    "image/jpg": True,
    "image/png": True,
    "audio/mp3": True,
    "audio/mp4": True,
    "video/quicktime": True,
}


def validate_request_limit(daily_limit: int, request_count: int) -> None:
    """Will throw ValueError if the request limit will be exceeded."""
    less_than_limit = request_count + 1 < daily_limit
    if not less_than_limit:
        raise ValueError("Daily limit has been reached.")


def validate_file_type(content_type: str) -> None:
    # get the file extension for the file
    """Will throw ValueError if the wrong type of file"""
    is_supported = ALLOWED_FILE_TYPES.get(content_type, False)
    if not is_supported:
        raise TypeError("That filetype is not supported.")


async def get_file(attachment: Attachment):
    match attachment.content_type:
        case "application/pdf", "text/plain; charset=utf-8":
            return "pdf"
        case "image/jpeg", "image/jpg", "image/png":
            return "image"
        case "audio/mp3", "audio/mp4", "video/quicktime":
            "audio/video"
