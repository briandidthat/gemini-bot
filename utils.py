from datetime import datetime, timedelta
from typing import IO, Dict, Optional, Type

from PIL import Image

from agent import File
from exception import DoneForTheDayException, FileProcessingException

ALLOWED_FILE_TYPES: Dict[str, bool] = {
    "application/pdf": False,
    "text/plain; charset=utf-8": True,
    "image/jpeg": True,
    "image/jpg": True,
    "image/png": True,
    "audio/mp3": True,
    "audio/mp4": True,
    "video/quicktime": True,
    "video/mp4": True,
    "video/mpeg": True,
    "video/mov": True,
    "video/avi": True,
    "video/x-flv": True,
    "video/mpg": True,
    "video/webm": True,
    "video/wmv": True,
    "video/3gpp": True,
}


def validate_request_limit(daily_limit: int, request_count: int) -> None:
    """Will throw DoneForTheDayException if the request limit will be exceeded."""
    less_than_limit = request_count + 1 < daily_limit
    if not less_than_limit:
        raise DoneForTheDayException(
            message="Daily limit has been reached.", type=type(ValueError).__name__
        )


def get_file(
    filename: str, content: IO, content_type: str
) -> File | Type[FileProcessingException]:
    """Create file instance from content and content type.
    Will throw FileProcessingException if the filetype is not supported.
    TODO: handle other file types

    Args:
        content: The file contents.
        content_type: The filetype of the file.

    Returns:
        The difference in hours as an integer
    """
    is_supported = ALLOWED_FILE_TYPES.get(content_type, False)
    if not is_supported:
        raise FileProcessingException(
            message="That filetype is not supported.", type=type(TypeError).__name__
        )

    match content_type:
        case "image/jpeg" | "image/jpg" | "image/png":
            try:
                image = Image.open(fp=content.fp)
                return File(filename, image, content_type)
            except Exception as e:
                raise FileProcessingException(message=str(e), type=type(e).__name__)
        case "audio/mp3" | "audio/mp4":
            try:
                file: File = None
                return file
            except Exception as e:
                raise FileProcessingException(message=str(e), type=type(e).__name__)
        case (
            "video/mp4"
            | "video/mpeg"
            | "video/mov"
            | "video/avi"
            | "video/x-flv"
            | "video/mpg"
            | "video/webm"
            | "video/wmv"
            | "video/3gpp"
        ):
            try:
                file: File = None
                return file
            except Exception as e:
                raise FileProcessingException(message=str(e), type=type(e).__name__)
        case _:
            raise FileProcessingException(
                f"Invalid file type. {content_type}", type="FileProcessingException"
            )


def get_time_delta(start: Optional[datetime], end: Optional[datetime]) -> Optional[int]:
    """Calculates the difference between two datetime objects in hours.

    Args:
        start: The first datetime object.
        end: The second datetime object.
    Returns:
        The difference in hours as an integer
    """
    if end is None or start is None:
        return None

    # Ensure end is always the later datetime
    if end < start:
        end, start = start, end

    delta: timedelta = end - start  # Calculate the timedelta
    total_seconds: int = int(delta.total_seconds())  # Convert to total seconds
    total_hours: int = int(round(total_seconds / 3600, 2))  # Convert to hours and round
    return total_hours
