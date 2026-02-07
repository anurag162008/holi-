# Jarvis-Style Assistant (Free, Self-Hosted)

This repo now includes a **working, single‑app prototype** that runs on **Windows 10/11 and Linux** and provides:

- ✅ Voice + Chat in one app
- ✅ System stats
- ✅ Weather
- ✅ Web search
- ✅ Optional automation (your own PC only)

> **Safety**: Automation and remote control should be used only on **your own device** with explicit consent.

---

## Quick start

### 1) Create and activate virtualenv

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

Automation is optional:

```bash
pip install -r requirements-automation.txt
```

### 3) Run the app

```bash
uvicorn app.main:app --reload --port 8000
```

Open: `http://localhost:8000`

---

## Desktop app (Windows / Linux)

This repo now ships a lightweight desktop UI that supports voice-ready chat, PC control hooks,
real-time search, and long-term memory storage.

### Run the desktop app

```bash
python -m desktop_app
```

### Optional dependencies

- **Whisper (STT)**: install `openai-whisper` and FFmpeg to use local speech-to-text.
- **Voice recording**: install `sounddevice` + `soundfile` for microphone capture.
- **Piper (TTS)**: install `piper` and `ffplay` (from FFmpeg) for female voice output.
- **PyAutoGUI**: install `pyautogui` for mouse/keyboard control.

### Memory storage

Use the **Select Memory Folder** button in the UI to choose where long-term memory is stored
(SQLite file inside that folder).

### Provider routing

The desktop app automatically tries providers in this order:

1. Ollama (local)
2. Gemini API
3. OpenRouter
4. Hugging Face Inference

Set environment variables to enable providers:

```bash
set LLM_PROVIDER=auto
set GEMINI_API_KEY=your_key
set OPENROUTER_API_KEY=your_key
set HF_API_KEY=your_key
```

On Linux/macOS:

```bash
export LLM_PROVIDER=auto
export GEMINI_API_KEY=your_key
export OPENROUTER_API_KEY=your_key
export HF_API_KEY=your_key
```

You can force a specific provider for the web app by setting `LLM_PROVIDER` to
`ollama`, `gemini`, `openrouter`, or `huggingface`.

---

## Features

### Voice + Chat (single app)
- Uses **Web Speech API** in the browser for voice input.
- Uses browser **TTS** for voice output.
- Chat replies are routed through optional LLM providers (Ollama/Gemini/OpenRouter/HF).
- Persona prompt is **editable in the UI** and saved in the browser.

### System stats
- CPU, RAM, disk, network (via `psutil`).

### Weather
- Uses **Open‑Meteo** (free, no API key required).

### Web search
- Uses **DuckDuckGo Instant Answer API**.

---

## Lightweight mode (2 GB RAM friendly)

This prototype is intentionally light and will run on low‑spec PCs if you keep it minimal:

- Use only `requirements.txt` (skip automation if not needed).
- Keep the browser tab count low and close other heavy apps.
- Avoid heavy AI models locally; use the built‑in web speech + TTS in the browser.

### Recommended low‑spec settings
- Run with a single worker (default).
- Do not enable automation unless needed.
- Use a lightweight browser (Edge/Firefox).

### What it can do right now (out of the box)
- Show **CPU/RAM/Disk/Network** stats.
- Fetch **live weather** by latitude/longitude.
- Do **web search** (DuckDuckGo).
- Basic **chat UI** with speech input + TTS output (browser).
- **Optional automation** (type, press keys, click) on your own PC only.
- Change the assistant persona prompt (default: “Divya”).

### Optional automation (your PC only)

Automation is **off by default**. Enable it by setting:

```bash
# Windows (PowerShell)
$env:ENABLE_AUTOMATION="1"

# Linux/macOS
ENABLE_AUTOMATION=1
```

Then call `/api/command` with:

```json
{
  "action": "type_text",
  "text": "hello",
  "confirm": true
}
```

Supported actions:
- `type_text`
- `press` (single key or list)
- `click` (x, y)

---

## API endpoints

- `GET /api/health`
- `GET /api/stats`
- `GET /api/weather?lat=..&lon=..`
- `GET /api/search?q=..`
- `POST /api/command` (automation)
- You can trigger automation from the web UI when `ENABLE_AUTOMATION=1` and `pyautogui` are available.
- `POST /api/transcribe` (optional Whisper STT, expects `audio_base64`)
- `POST /api/speak` (optional Piper TTS)

---

## Next steps

If you want a more advanced build (offline STT/TTS, multi‑agent, memory, etc.), I can:

- Wire Whisper.cpp / Vosk for offline STT
- Wire Piper for offline TTS
- Add more tool routing (desktop automation, scheduling, reminders)
- Add RustDesk/VNC setup guide for remote desktop

---

## License

MIT (add your own license as needed)
