from datetime import time
from discord.ext import commands, tasks
from google.generativeai import GenerativeModel


class Agent:
    def __init__(self, model_name: str, daily_limit: int) -> None:
        self.__model = GenerativeModel(model_name)
        self.__daily_limit = daily_limit
        self.__request_count = 0

    def set_new_model(self, model_name: str):
        self.__model = GenerativeModel(model_name)

    def set_daily_limit(self, daily_limit: int):
        self.__daily_limit = daily_limit

    def get_request_count(self) -> int:
        return self.__request_count

    def get_model_name(self) -> str:
        return self.__model.model_name

    def reset_request_count(self) -> None:
        self.__request_count = 0

    def validate_limit(self) -> bool:
        if self.__request_count + 1 >= self.__daily_limit:
            return False
        return True

    def generate_content(self, prompt: str) -> str:
        if not self.validate_limit():
            raise ValueError("Daily limit has been reached.")

        if len(prompt) >= 1000:
            raise ValueError("Prompt is over 1k characters.")

        response = self.__model.generate_content(prompt)
        self.__request_count += 1

        return response.text


scheduled_time = time(hour=0, minute=0, second=0)


class AgentCog(commands.Cog):
    def __init__(self, agent: Agent):
        self.__agent = agent

    @tasks.loop(time=scheduled_time)
    async def reset_count_task(self):
        print("Resetting request count to 0.")
        self.__agent.reset_request_count()
