#!/usr/bin/env python3
import os
import re
import json
import argparse
import asyncio
from typing import List, Dict, Any, Optional

# Optional OpenAI import (we'll handle absence gracefully)
try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

# AMS SDK (async)
try:
    from agent_memory_client import MemoryAPIClient, MemoryClientConfig
except Exception:  # pragma: no cover
    MemoryAPIClient = None  # type: ignore
    MemoryClientConfig = None  # type: ignore

import urllib.request
import urllib.error


def ping_url(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


class LocalMemoryFallback:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.path = f".local_memory_{user_id}.json"
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception:
            self.data = {"long_term": []}

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    async def create_long_term_memory(self, items: List[Dict[str, Any]]):
        for it in items:
            it = dict(it)
            it["user_id"] = self.user_id
            self.data["long_term"].append(it)
        self._save()

    async def search_long_term_memory(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:
        # naive relevance: return most recent up to limit
        return list(reversed(self.data.get("long_term", [])))[:limit]


class AMSClientWrapper:
    def __init__(self, base_url: str, user_id: str):
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.available = False
        self.client: Optional[Any] = None

    async def init(self):
        global MemoryAPIClient, MemoryClientConfig
        health = f"{self.base_url}/health"
        if ping_url(health) and MemoryAPIClient and MemoryClientConfig:
            try:
                self.client = MemoryAPIClient(MemoryClientConfig(base_url=self.base_url))
                self.available = True
                return
            except Exception:
                pass
        # Fallback to local file memory
        self.client = LocalMemoryFallback(self.user_id)
        self.available = False

    async def create_long_term_memory(self, items: List[Dict[str, Any]]):
        if hasattr(self.client, "create_long_term_memory"):
            return await self.client.create_long_term_memory(items)
        raise RuntimeError("No memory backend available")

    async def search_long_term_memory(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:
        if hasattr(self.client, "search_long_term_memory"):
            return await self.client.search_long_term_memory(text=text, user_id=self.user_id) if self.available else await self.client.search_long_term_memory(text, limit)
        return []


def extract_user_details(text: str) -> List[Dict[str, Any]]:
    details: List[Dict[str, Any]] = []
    # name
    m = re.search(r"\bmy name is\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b", text, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        details.append({
            "text": f"User's name is {name}.",
            "memory_type": "profile",
            "metadata": {"field": "name", "value": name}
        })
    # email
    m = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    if m:
        email = m.group(0)
        details.append({
            "text": f"User's email is {email}.",
            "memory_type": "profile",
            "metadata": {"field": "email", "value": email}
        })
    # location
    m = re.search(r"\bI\s*(?:am|\'m|am)\s*(?:in|at)\s+([A-Za-z][A-Za-z\s,]+)\b|\bI\s*live\s*(?:in|at)\s+([A-Za-z][A-Za-z\s,]+)\b", text, re.IGNORECASE)
    if m:
        loc = (m.group(1) or m.group(2) or "").strip().rstrip(".,!")
        if loc:
            details.append({
                "text": f"User is located in {loc}.",
                "memory_type": "profile",
                "metadata": {"field": "location", "value": loc}
            })
    # preferences
    pref = re.search(r"\bI\s*(?:like|love|prefer|enjoy)\s+([^\.\n!]+)", text, re.IGNORECASE)
    if pref:
        val = pref.group(1).strip().rstrip(".,!")
        details.append({
            "text": f"User prefers {val}.",
            "memory_type": "preference",
            "metadata": {"field": "preference", "value": val}
        })
    return details


def summarize_memories(memories: List[Dict[str, Any]]) -> str:
    lines = []
    for m in memories:
        txt = m.get("text") or json.dumps(m)
        lines.append(f"- {txt}")
    return "\n".join(lines) if lines else "(none)"


async def call_llm(messages: List[Dict[str, str]]) -> str:
    # Try OpenAI first
    if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
        try:
            client = OpenAI()
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"[LLM error: {e}]\n\nYou said: {messages[-1]['content']}"
    # Fallback: simple echo
    user_text = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    memory_text = next((m["content"] for m in messages if m["role"] == "system" and m["content"].startswith("Known user details")), "")
    return f"(offline) I don't have an LLM key configured.\n{memory_text}\n\nYou said: {user_text}"


async def chat_loop(ams: AMSClientWrapper, user_id: str, session_id: str):
    print("Type 'exit' to quit.\n")
    while True:
        try:
            user = input("You: ").strip()
        except EOFError:
            break
        if not user:
            continue
        if user.lower() in {"exit", "quit"}:
            break

        # Retrieve relevant long-term memories
        try:
            memories = await ams.search_long_term_memory(text=user, limit=5)
        except Exception:
            memories = []
        mem_summary = summarize_memories(memories)

        # Build messages for LLM
        system = "Known user details (from memory):\n" + mem_summary
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        reply = await call_llm(messages)
        print(f"Assistant: {reply}\n")

        # Extract and store any new user details in memory (long-term)
        extracted = extract_user_details(user)
        if extracted:
            # Add user_id to each
            for it in extracted:
                it["user_id"] = user_id
            try:
                await ams.create_long_term_memory(extracted)
                print(f"[stored {len(extracted)} memory item(s)]")
            except Exception as e:
                print(f"[warning] failed to store memory: {e}")


async def main_async():
    parser = argparse.ArgumentParser(description="Simple CLI chat with Redis Agent Memory Server integration")
    parser.add_argument("--ams-url", default=os.getenv("AMS_BASE_URL", "http://localhost:8000"), help="Agent Memory Server base URL")
    parser.add_argument("--user-id", default=os.getenv("USER_ID", "user123"), help="User ID")
    parser.add_argument("--session-id", default=os.getenv("SESSION_ID", "session1"), help="Session ID")
    args = parser.parse_args()

    ams = AMSClientWrapper(args.ams_url, args.user_id)
    await ams.init()
    if ams.available:
        print(f"Connected to AMS at {args.ams_url} (remote backend)")
    else:
        print(f"AMS not available at {args.ams_url}. Using local file memory fallback.")

    if not os.getenv("OPENAI_API_KEY"):
        print("Note: OPENAI_API_KEY not set. Falling back to offline echo mode. Set OPENAI_API_KEY to use an LLM.")

    await chat_loop(ams, args.user_id, args.session_id)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
