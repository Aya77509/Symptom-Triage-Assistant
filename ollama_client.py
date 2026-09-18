"""
Tiny wrapper around the local Ollama REST API. No extra SDK needed -
just `requests`. Requires Ollama running locally (`ollama serve`, usually
already running after install) and the model pulled:

    ollama pull llama3.2

If you'd rather use the official `ollama` python package, you can swap
this file's internals later without touching extract.py / baseline.py.
"""

import json
import requests

from config import OLLAMA_HOST, MODEL_NAME


def chat(prompt: str, system: str = "", json_mode: bool = False, temperature: float = 0.1) -> str:
    """Send a single-turn prompt to the local model, return the text response."""
    payload = {
        "model": MODEL_NAME,
        "messages": (
            ([{"role": "system", "content": system}] if system else [])
            + [{"role": "user", "content": prompt}]
        ),
        "stream": False,
        "options": {"temperature": temperature},
    }
    if json_mode:
        payload["format"] = "json"

    resp = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def extract_json(text: str) -> dict:
    """Best-effort extraction of a JSON object from a model response,
    in case the model wraps it in markdown fences or extra text."""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model output:\n{text}")
    return json.loads(text[start : end + 1])
