import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-pro-latest")

# response = model.generate_content("Describe the role of a Product Manager in the software engineering sector.")
# print(response.text)