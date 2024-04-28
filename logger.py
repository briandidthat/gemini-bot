import logging

from pythonjsonlogger import jsonlogger


handler = logging.StreamHandler(stream=None)
handler.setFormatter(
    jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
