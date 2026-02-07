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

## Features

### Voice + Chat (single app)
- Uses **Web Speech API** in the browser for voice input.
- Uses browser **TTS** for voice output.
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

---

## Next steps

If you want a more advanced build (offline STT/TTS, multi‑agent, memory, etc.), I can:

- Wire Whisper.cpp / Vosk for offline STT
- Wire Piper for offline TTS
- Add a real LLM back‑end and tool routing
- Add RustDesk/VNC setup guide for remote desktop

---

## License

MIT (add your own license as needed)
