import os
import google.generativeai as genai

from agent import Agent

# configure google genai
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])


gemini_agent = Agent(model_name="gemini-1.0-pro-latest", daily_limit=1500)

content = gemini_agent.generate_content(
    "Generate a list of the 5 most critically acclaimed american horror movies of all time."
)

print(content)
