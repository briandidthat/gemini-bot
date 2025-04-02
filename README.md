# Gemini-Powered Discord Bot

Enhance your Discord server with a powerful conversational AI chatbot backed by Google's Gemini API.

## Features

- Conversational AI: The bot uses Google's Gemini API to generate human-like text responses.
- User-specific chat history: The bot maintains a separate chat history for each user to provide a more personalized experience.
- File processing capabilities. The bot is able to recieve an file as input and process it along with the prompt.

## How to Get Started

1. Create a bot account and invite it to your channel:

   - Tutorial: [Create a bot account](https://discordpy.readthedocs.io/en/stable/discord.html)

2. Obtain API Keys:

   - Gemini API Key. Head over to [AI Studio](https://aistudio.google.com/app/apikey).
   - Discord API Key. Head over to [Discord Developer Portal](https://discord.com/developers/applications).

3. Head over to your deployment infrastructure of choice and define the following environment variables:

   - `BOT_OWNER`: The owner/administrator of the bot
   - `CHAT_TTL`: The time-to-live (TTL) for each chat in days. A process is run every 6 hours to delete any inactive chat above the ttl
   - `DAILY_LIMIT`: The daily limit to the amount of requests your gemini agent will accept.
   - `DISCORD_TOKEN`: Your Discord API Key.
   - `GOOGLE_API_KEY`: Your Gemini API Key.

4. Deploy the [Gemini-Bot](https://hub.docker.com/repository/docker/briandidthat/gemini-bot/general) image to your infrastructure of choice (or local using Docker).

The bot will now be online and ready to interact in your Discord server.

## Usage

To interact with the bot, mention it in a message in your Discord server. The bot will respond with a generated message.

## Logging

The bot uses Python's `logging` module to log events. It uses the `python-json-logger` package to format the logs as JSON. The logs can be found in the console output.
