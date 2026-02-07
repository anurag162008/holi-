from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class AppConfig:
    persona_name: str = "Divya"
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    llm_provider: str = os.getenv("LLM_PROVIDER", "auto")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    hf_api_key: str | None = os.getenv("HF_API_KEY")
    hf_model: str = os.getenv("HF_MODEL", "google/flan-t5-large")
    whisper_model: str = os.getenv("WHISPER_MODEL", "base")
    piper_voice: str = os.getenv("PIPER_VOICE", "en_US-amy-low")
    voice_record_seconds: int = int(os.getenv("VOICE_RECORD_SECONDS", "5"))
    voice_sample_rate: int = int(os.getenv("VOICE_SAMPLE_RATE", "16000"))
    auto_speak: bool = os.getenv("AUTO_SPEAK", "1") != "0"


DEFAULT_SYSTEM_PROMPT = (
    "You are Divya, a polite, helpful AI assistant with a warm, friendly tone. "
    "You are a Jarvis-style system controller for the user's own PC. "
    "Always ask for confirmation before any risky action."
)
