AMS Preferences App

This is a minimal chat-style demo that uses Redis Agent Memory Server (AMS) to automatically extract and surface salient user preferences.

What it does
- Runs AMS + Redis via docker-compose
- Sends user chat messages to AMS working memory
- Enables the built-in "preferences" extraction strategy
- Queries long-term memory for extracted preference memories

Requirements
- Docker + Docker Compose
- An LLM provider key supported by LiteLLM (e.g., OPENAI_API_KEY)

Quick start
1) Copy .env.example to .env and fill values.
2) docker compose up -d
3) python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
4) python app.py

Type a few messages that imply preferences (e.g., "I only drink oat milk", "I prefer morning workouts"). Then press \"p\" to print detected preferences.
