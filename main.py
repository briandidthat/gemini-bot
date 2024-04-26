import os
import google.generativeai as genai

from agent import Agent, AgentCog

# configure google genai
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# initialize Agent instance for content generation
gemini_agent = Agent(model_name="gemini-1.0-pro-latest", daily_limit=1500)
# initialize AgentCog instance for daily resetting of request count
gemini_agent_cog = AgentCog(gemini_agent)

content = gemini_agent.generate_content(
    "Generate a list of the 5 most critically acclaimed american horror movies of all time."
)

print(content)
