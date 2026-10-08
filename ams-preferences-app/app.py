import asyncio
import os
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
NAMESPACE = os.getenv("NAMESPACE", "demo")
USER_ID = os.getenv("USER_ID", "user123")
SESSION_ID = os.getenv("SESSION_ID", "session123")

console = Console()

async def add_message(client: httpx.AsyncClient, role: str, content: str) -> None:
    # AMS expects created_at timestamps; provide them to avoid warnings
    payload = {
        "namespace": NAMESPACE,
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "messages": [
            {
                "role": role,
                "content": content,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ],
        # Tell AMS to use the preferences extraction strategy for this session
        "extraction": {"strategy": "preferences", "config": {}},
    }
    r = await client.post(f"{BASE_URL}/v1/working-memory/update", json=payload)
    r.raise_for_status()

async def get_preferences(client: httpx.AsyncClient):
    # Query long-term memory for type preference via hybrid search
    # Preference records are stored as long-term memories with topics/entities/tags
    payload = {
        "namespace": NAMESPACE,
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "search_mode": "hybrid",
        "text": "user preferences",
        "limit": 20,
        # You can filter by strategy-specific tags; keep it simple for demo
    }
    r = await client.post(f"{BASE_URL}/v1/long-term-memory/search", json=payload)
    r.raise_for_status()
    return r.json()

async def main():
    console.print("[bold green]AMS Preferences Demo[/bold green]")
    console.print("Type messages about your likes/dislikes.\nCommands: /prefs to view extracted preferences, /quit to exit.")

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            text = input("you> ").strip()
            if not text:
                continue
            if text in ("/quit", "/exit"):
                break
            if text == "/prefs":
                data = await get_preferences(client)
                items = data.get("items") or data.get("memories") or []
                if not items:
                    console.print("[yellow]No preferences found yet. Keep chatting![/yellow]")
                    continue
                table = Table(show_lines=True)
                table.add_column("Score", justify="right")
                table.add_column("Text")
                table.add_column("Topics/Entities")
                for it in items:
                    text = it.get("text") or it.get("content") or ""
                    score = f"{it.get('score', 0):.3f}" if isinstance(it.get("score"), (int, float)) else str(it.get("score", ""))
                    topics = ", ".join(it.get("topics", []) or [])
                    ents = ", ".join((it.get("entities", []) or []))
                    table.add_row(str(score), text, "; ".join([t for t in [topics, ents] if t]))
                console.print(table)
                continue
            # Default path: add user message and let AMS extract preferences
            await add_message(client, role="user", content=text)
            console.print("[dim]sent[/dim]")

if __name__ == "__main__":
    asyncio.run(main())
