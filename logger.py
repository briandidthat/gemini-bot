import logging

from pythonjsonlogger import jsonlogger


handler = logging.StreamHandler(stream=None)
handler.setFormatter(
    jsonlogger.JsonFormatter(
        fmt="%(name)s %(asctime)s %(levelname)s %(message)s",
        rename_fields={"name": "logger", "asctime": "timestamp", "levelname": "level"},
    )
)

bot_logger = logging.getLogger("bot-logger")
bot_logger.addHandler(handler)
bot_logger.setLevel(logging.INFO)


agent_logger = logging.getLogger("agent-logger")
agent_logger.addHandler(handler)
agent_logger.setLevel(logging.INFO)
