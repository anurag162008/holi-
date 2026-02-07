from __future__ import annotations

import subprocess
from typing import Any

from desktop_app.config import AppConfig
from desktop_app.providers import is_module_available, load_module


class SpeechEngine:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def record_audio(self, output_path: str) -> None:
        if not is_module_available("sounddevice"):
            raise RuntimeError("sounddevice is required for voice recording")
        sounddevice = load_module("sounddevice")
        soundfile = load_module("soundfile")
        recording = sounddevice.rec(
            int(self.config.voice_record_seconds * self.config.voice_sample_rate),
            samplerate=self.config.voice_sample_rate,
            channels=1,
        )
        sounddevice.wait()
        soundfile.write(output_path, recording, self.config.voice_sample_rate)

    def transcribe(self, audio_path: str) -> str:
        whisper = load_module("whisper")
        model = whisper.load_model(self.config.whisper_model)
        result: dict[str, Any] = model.transcribe(audio_path)
        return result.get("text", "").strip()

    def speak(self, text: str) -> None:
        command = [
            "piper",
            "--model",
            self.config.piper_voice,
            "--output_file",
            "speech.wav",
        ]
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        if process.stdin is not None:
            process.stdin.write(text.encode("utf-8"))
            process.stdin.close()
        process.wait()
        self._play_audio("speech.wav")

    def _play_audio(self, path: str) -> None:
        if subprocess.call(["ffplay", "-nodisp", "-autoexit", path]) != 0:
            raise RuntimeError("ffplay is required to play audio")
