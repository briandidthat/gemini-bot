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


gemini_agent_logger = logging.getLogger("gemini-agent")
gemini_agent_logger.addHandler(handler)
gemini_agent_logger.setLevel(logging.INFO)
