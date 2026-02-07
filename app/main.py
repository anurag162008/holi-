import base64
import importlib.util
import json
import os
import shutil
import tempfile
from datetime import datetime
from typing import Any

import psutil
import requests
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import subprocess

from app.llm import DEFAULT_SYSTEM_PROMPT, LLMRouter

pyautogui = None
if importlib.util.find_spec("pyautogui") is not None:
    import pyautogui as pyautogui  # type: ignore

app = FastAPI(title="Jarvis Assistant")
router = LLMRouter()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")


def get_stats() -> dict[str, float]:
    return {
        "cpu": psutil.cpu_percent(interval=0.2),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "net_sent_mb": round(psutil.net_io_counters().bytes_sent / 1_048_576, 2),
        "net_recv_mb": round(psutil.net_io_counters().bytes_recv / 1_048_576, 2),
    }


def fetch_weather(lat: float, lon: float) -> dict[str, Any]:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current_weather=true"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_search(q: str) -> dict[str, Any]:
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


def build_system_prompt(persona: str) -> str:
    if not persona:
        return DEFAULT_SYSTEM_PROMPT
    return f"{DEFAULT_SYSTEM_PROMPT}\nPersona: {persona}"


def normalize_memory_path(path: str) -> str:
    expanded = os.path.expanduser(path.strip())
    return os.path.abspath(expanded)


def append_memory(path: str, payload: dict[str, Any]) -> None:
    os.makedirs(path, exist_ok=True)
    memory_file = os.path.join(path, "jarvis_memory.jsonl")
    with open(memory_file, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_memory(path: str, limit: int = 50) -> list[dict[str, Any]]:
    memory_file = os.path.join(path, "jarvis_memory.jsonl")
    if not os.path.exists(memory_file):
        return []
    with open(memory_file, "r", encoding="utf-8") as handle:
        lines = handle.readlines()[-limit:]
    return [json.loads(line) for line in lines if line.strip()]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/stats")
def stats() -> dict[str, float]:
    return get_stats()


@app.get("/api/weather")
def weather(lat: float, lon: float) -> dict[str, Any]:
    return fetch_weather(lat, lon)


@app.get("/api/search")
def search(q: str) -> dict[str, Any]:
    return fetch_search(q)


@app.post("/api/chat")
def chat(payload: dict[str, Any]) -> dict[str, Any]:
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    persona = str(payload.get("persona", "")).strip()
    lat = payload.get("lat")
    lon = payload.get("lon")
    memory_path = str(payload.get("memory_path", "")).strip()
    lower_message = message.lower()
    memory_root = None
    if memory_path:
        memory_root = normalize_memory_path(memory_path)

    if "stats" in lower_message or "status" in lower_message:
        stats_payload = get_stats()
        reply = (
            "Here are the latest system stats. "
            f"CPU {stats_payload['cpu']}%, RAM {stats_payload['ram']}%, "
            f"Disk {stats_payload['disk']}%."
        )
        if memory_root:
            timestamp = datetime.utcnow().isoformat()
            append_memory(
                memory_root,
                {"timestamp": timestamp, "role": "user", "message": message, "persona": persona},
            )
            append_memory(
                memory_root,
                {"timestamp": timestamp, "role": "assistant", "message": reply, "persona": persona},
            )
        return {"reply": reply, "data": {"stats": stats_payload, "persona": persona}}

    if "weather" in lower_message:
        if lat is None or lon is None:
            raise HTTPException(status_code=400, detail="lat and lon are required for weather")
        weather_payload = fetch_weather(float(lat), float(lon))
        current = weather_payload.get("current_weather") or {}
        reply = (
            "Here's the current weather. "
            f"Temperature {current.get('temperature')}°C, "
            f"Wind {current.get('windspeed')} km/h."
        )
        if memory_root:
            timestamp = datetime.utcnow().isoformat()
            append_memory(
                memory_root,
                {"timestamp": timestamp, "role": "user", "message": message, "persona": persona},
            )
            append_memory(
                memory_root,
                {"timestamp": timestamp, "role": "assistant", "message": reply, "persona": persona},
            )
        return {"reply": reply, "data": {"weather": weather_payload, "persona": persona}}

    if "search" in lower_message:
        query = message.split("search", 1)[1].strip(" :") if "search" in lower_message else ""
        query = query or message
        search_payload = fetch_search(query)
        summary = search_payload.get("answer") or search_payload.get("abstract") or "I found some results."
        reply = f"Search results for '{query}': {summary}"
        if memory_root:
            timestamp = datetime.utcnow().isoformat()
            append_memory(
                memory_root,
                {"timestamp": timestamp, "role": "user", "message": message, "persona": persona},
            )
            append_memory(
                memory_root,
                {"timestamp": timestamp, "role": "assistant", "message": reply, "persona": persona},
            )
        return {"reply": reply, "data": {"search": search_payload, "persona": persona}}

    system_prompt = build_system_prompt(persona)
    try:
        reply = router.generate(message, system_prompt=system_prompt, need_reasoning=True)
    except RuntimeError:
        reply = (
            "I'm having trouble reaching the AI provider right now. "
            "Please check your provider settings or try again later."
        )
    if memory_root:
        timestamp = datetime.utcnow().isoformat()
        append_memory(
            memory_root,
            {"timestamp": timestamp, "role": "user", "message": message, "persona": persona},
        )
        append_memory(
            memory_root,
            {"timestamp": timestamp, "role": "assistant", "message": reply, "persona": persona},
        )
    return {"reply": reply, "data": {"persona": persona}}


@app.get("/api/memory")
def memory(path: str) -> dict[str, Any]:
    if not path.strip():
        raise HTTPException(status_code=400, detail="path is required")
    memory_root = normalize_memory_path(path)
    return {"path": memory_root, "entries": read_memory(memory_root)}


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
def transcribe(payload: dict[str, Any]) -> dict[str, str]:
    if importlib.util.find_spec("whisper") is None:
        raise HTTPException(status_code=501, detail="Whisper is not installed")
    import whisper  # type: ignore
    audio_base64 = str(payload.get("audio_base64", "")).strip()
    if not audio_base64:
        raise HTTPException(status_code=400, detail="audio_base64 is required")
    if audio_base64.startswith("data:"):
        audio_base64 = audio_base64.split(",", 1)[-1]
    filename = str(payload.get("filename", "audio.wav"))
    suffix = os.path.splitext(filename)[1] or ".wav"
    try:
        audio_bytes = base64.b64decode(audio_base64)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="audio_base64 must be valid base64") from exc
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(audio_bytes)
        temp_path = handle.name
    model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))
    result: dict[str, Any] = model.transcribe(temp_path)
    os.unlink(temp_path)
    return {"text": result.get("text", "").strip()}


@app.post("/api/speak")
def speak(payload: dict[str, Any]) -> dict[str, str]:
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    voice = os.getenv("PIPER_VOICE", "en_US-amy-low")
    if not shutil.which("piper"):
        raise HTTPException(status_code=501, detail="piper is not installed")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as handle:
        output_path = handle.name
    process = subprocess.run(
        ["piper", "--model", voice, "--output_file", output_path],
        input=text.encode("utf-8"),
        check=False,
    )
    if process.returncode != 0:
        os.unlink(output_path)
        raise HTTPException(status_code=500, detail="piper failed to synthesize audio")
    with open(output_path, "rb") as handle:
        audio_bytes = handle.read()
    os.unlink(output_path)
    return {"audio_base64": base64.b64encode(audio_bytes).decode("utf-8")}
