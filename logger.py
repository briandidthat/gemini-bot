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


chat_agent_logger = logging.getLogger("chat-agent")
chat_agent_logger.addHandler(handler)
chat_agent_logger.setLevel(logging.INFO)


vision_agent_logger = logging.getLogger("vision-agent")
vision_agent_logger.addHandler(handler)
vision_agent_logger.setLevel(logging.INFO)
