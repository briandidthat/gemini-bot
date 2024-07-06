from typing import IO, Dict, Type


from PIL import Image

from agent import File
from exception import DoneForTheDayException, FileProcessingException


# Will definitely be changing to True, but WIP
ALLOWED_FILE_TYPES: Dict[str, bool] = {
    "application/pdf": False,
    "text/plain; charset=utf-8": True,
    "image/jpeg": True,
    "image/jpg": True,
    "image/png": True,
    "audio/mp3": False,
    "audio/mp4": False,
    "video/quicktime": False,
}


def validate_request_limit(daily_limit: int, request_count: int) -> None:
    """Will throw ValueError if the request limit will be exceeded."""
    less_than_limit = request_count + 1 < daily_limit
    if not less_than_limit:
        raise DoneForTheDayException(
            message="Daily limit has been reached.", type=type(ValueError).__name__
        )


def get_file(content: IO, content_type: str) -> File | Type[FileProcessingException]:
    """
    Create file instance from content and content type. Only supporting images for now.
    Will throw FileProcessingException if the filetype is not supported.
    TODO: handle other file types
    """
    is_supported = ALLOWED_FILE_TYPES.get(content_type, False)
    if not is_supported:
        raise FileProcessingException(
            message="That filetype is not supported.", type=type(TypeError).__name__
        )

    match content_type:
        case "image/jpeg" | "image/jpg" | "image/png":
            try:
                file: File = process_image(content.name, content, content_type)
                return file
            except Exception as e:
                raise FileProcessingException(message=str(e), type=type(e).__name__)

        case _:
            raise FileProcessingException(
                f"Invalid file type. {content_type}", type="FileProcessingException"
            )


def process_image(file_name: str, content: IO, content_type: str) -> File:
    image = Image.open(fp=content.fp)
    return File(file_name, image, content_type)
