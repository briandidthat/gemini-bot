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


def get_file(file: IO, content_type: str) -> File | Type[FileProcessingException]:
    is_supported = ALLOWED_FILE_TYPES.get(content_type, False)
    if not is_supported:
        raise FileProcessingException(
            message="That filetype is not supported.", type=type(TypeError).__name__
        )

    match content_type:
        case "image/jpeg", "image/jpg", "image/png":
            try:
                image = Image.open(fp=file.fp)
                return File(image, content_type)
            except Exception as e:
                raise FileProcessingException(message=str(e), type=type(e).__name__)

        case _:
            raise FileProcessingException(
                "Invalid file type", type="FileProcessingException"
            )
