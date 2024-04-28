import logging

from pythonjsonlogger import jsonlogger


handler = logging.StreamHandler(stream=None)
handler.setFormatter(
    jsonlogger.JsonFormatter(
        fmt="%(name)s %(asctime)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
)

logger = logging.getLogger("MainLogger")
logger.addHandler(handler)
logger.setLevel(logging.INFO)


agent_logger = logging.getLogger("AgentLogger")
agent_logger.addHandler(handler)
agent_logger.setLevel(logging.INFO)
