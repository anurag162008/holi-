import os
from typing import Any

import psutil
import requests
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

try:
    import pyautogui  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pyautogui = None

app = FastAPI(title="Jarvis Assistant")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/stats")
def stats() -> dict[str, float]:
    return {
        "cpu": psutil.cpu_percent(interval=0.2),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "net_sent_mb": round(psutil.net_io_counters().bytes_sent / 1_048_576, 2),
        "net_recv_mb": round(psutil.net_io_counters().bytes_recv / 1_048_576, 2),
    }


@app.get("/api/weather")
def weather(lat: float, lon: float) -> dict[str, Any]:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current_weather=true"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


@app.get("/api/search")
def search(q: str) -> dict[str, Any]:
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query is required")
    response = requests.get(
        "https://api.duckduckgo.com/",
        params={"q": q, "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "heading": data.get("Heading"),
        "abstract": data.get("Abstract"),
        "answer": data.get("Answer"),
        "related": [item.get("Text") for item in data.get("RelatedTopics", []) if item.get("Text")],
    }


@app.post("/api/command")
def command(payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action")
    confirm = payload.get("confirm") is True
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to execute commands")
    if os.getenv("ENABLE_AUTOMATION") != "1":
        raise HTTPException(status_code=403, detail="Automation disabled. Set ENABLE_AUTOMATION=1")
    if pyautogui is None:
        raise HTTPException(status_code=500, detail="pyautogui not installed")

    if action == "type_text":
        text = payload.get("text", "")
        pyautogui.write(text)
        return {"status": "typed", "text": text}
    if action == "press":
        keys = payload.get("keys")
        if isinstance(keys, list):
            pyautogui.hotkey(*keys)
        elif isinstance(keys, str):
            pyautogui.press(keys)
        else:
            raise HTTPException(status_code=400, detail="keys must be string or list")
        return {"status": "pressed", "keys": keys}
    if action == "click":
        x = payload.get("x")
        y = payload.get("y")
        if x is None or y is None:
            raise HTTPException(status_code=400, detail="x and y are required")
        pyautogui.click(x, y)
        return {"status": "clicked", "x": x, "y": y}

    raise HTTPException(status_code=400, detail="Unsupported action")


@app.post("/api/transcribe")
def transcribe() -> dict[str, str]:
    raise HTTPException(status_code=501, detail="STT not wired yet")


@app.post("/api/speak")
def speak() -> dict[str, str]:
    raise HTTPException(status_code=501, detail="TTS not wired yet")
