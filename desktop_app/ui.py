from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from desktop_app.config import AppConfig
from desktop_app.intent import detect_intent
from desktop_app.memory import MemoryStore
from desktop_app.pc_control import close_app, control_input, open_app, open_path, set_brightness, set_volume
from desktop_app.providers import LLMRouter
from desktop_app.realtime import search_news, search_web, weather
from desktop_app.speech import SpeechEngine


class JarvisUI:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.router = LLMRouter(config)
        self.memory = MemoryStore(root_path="jarvis_memory")
        self.speech = SpeechEngine(config)
        self.root = tk.Tk()
        self.root.title("Jarvis Desktop Assistant")
        self.provider_var = tk.StringVar(value=self.config.llm_provider)
        self.ollama_host_var = tk.StringVar(value=self.config.ollama_host)
        self.gemini_key_var = tk.StringVar(value=self.config.gemini_api_key or "")
        self.openrouter_key_var = tk.StringVar(value=self.config.openrouter_api_key or "")
        self.openrouter_model_var = tk.StringVar(value=self.config.openrouter_model)
        self.hf_key_var = tk.StringVar(value=self.config.hf_api_key or "")
        self.hf_model_var = tk.StringVar(value=self.config.hf_model)
        self.auto_speak_var = tk.BooleanVar(value=self.config.auto_speak)

        self.chat_log = scrolledtext.ScrolledText(self.root, height=18, width=80)
        self.chat_log.pack(padx=12, pady=8)

        self.entry = tk.Entry(self.root, width=70)
        self.entry.pack(padx=12, pady=4, side=tk.LEFT)

        send_button = tk.Button(self.root, text="Send", command=self.on_send)
        send_button.pack(padx=4, pady=4, side=tk.LEFT)

        voice_button = tk.Button(self.root, text="🎤 Voice", command=self.on_voice)
        voice_button.pack(padx=4, pady=4, side=tk.LEFT)

        memory_button = tk.Button(self.root, text="Select Memory Folder", command=self.select_memory_folder)
        memory_button.pack(padx=4, pady=4, side=tk.LEFT)

        settings_frame = tk.LabelFrame(self.root, text="Settings")
        settings_frame.pack(padx=12, pady=8, fill=tk.X)

        provider_row = tk.Frame(settings_frame)
        provider_row.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(provider_row, text="LLM Provider").pack(side=tk.LEFT)
        provider_menu = tk.OptionMenu(
            provider_row,
            self.provider_var,
            "auto",
            "ollama",
            "gemini",
            "openrouter",
            "huggingface",
        )
        provider_menu.pack(side=tk.LEFT, padx=6)

        ollama_row = tk.Frame(settings_frame)
        ollama_row.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(ollama_row, text="Ollama Host").pack(side=tk.LEFT)
        tk.Entry(ollama_row, textvariable=self.ollama_host_var, width=50).pack(side=tk.LEFT, padx=6)

        gemini_row = tk.Frame(settings_frame)
        gemini_row.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(gemini_row, text="Gemini API Key").pack(side=tk.LEFT)
        tk.Entry(gemini_row, textvariable=self.gemini_key_var, width=50, show="*").pack(side=tk.LEFT, padx=6)

        openrouter_row = tk.Frame(settings_frame)
        openrouter_row.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(openrouter_row, text="OpenRouter API Key").pack(side=tk.LEFT)
        tk.Entry(openrouter_row, textvariable=self.openrouter_key_var, width=50, show="*").pack(
            side=tk.LEFT, padx=6
        )

        openrouter_model_row = tk.Frame(settings_frame)
        openrouter_model_row.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(openrouter_model_row, text="OpenRouter Model").pack(side=tk.LEFT)
        tk.Entry(openrouter_model_row, textvariable=self.openrouter_model_var, width=50).pack(side=tk.LEFT, padx=6)

        hf_row = tk.Frame(settings_frame)
        hf_row.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(hf_row, text="HF API Key").pack(side=tk.LEFT)
        tk.Entry(hf_row, textvariable=self.hf_key_var, width=50, show="*").pack(side=tk.LEFT, padx=6)

        hf_model_row = tk.Frame(settings_frame)
        hf_model_row.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(hf_model_row, text="HF Model").pack(side=tk.LEFT)
        tk.Entry(hf_model_row, textvariable=self.hf_model_var, width=50).pack(side=tk.LEFT, padx=6)

        auto_speak_row = tk.Frame(settings_frame)
        auto_speak_row.pack(fill=tk.X, padx=6, pady=4)
        tk.Checkbutton(auto_speak_row, text="Auto speak replies", variable=self.auto_speak_var).pack(
            side=tk.LEFT
        )
        tk.Button(auto_speak_row, text="Save Settings", command=self.save_settings).pack(side=tk.LEFT, padx=8)

    def select_memory_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.memory.set_root(folder)
            messagebox.showinfo("Memory", f"Memory folder set to {folder}")

    def on_send(self) -> None:
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self._append_chat("You", text)
        self.memory.add_session("user", text)
        threading.Thread(target=self._handle_message, args=(text,), daemon=True).start()

    def on_voice(self) -> None:
        threading.Thread(target=self._handle_voice, daemon=True).start()

    def _handle_voice(self) -> None:
        try:
            self._append_chat("System", "Listening...")
            self.speech.record_audio("voice_input.wav")
            text = self.speech.transcribe("voice_input.wav")
            if not text:
                self._append_chat("System", "I didn't catch that. Try again.")
                return
            self._append_chat("You", text)
            self.memory.add_session("user", text)
            self._handle_message(text)
        except Exception as exc:  # noqa: BLE001
            self._append_chat("System", f"Voice error: {exc}")

    def _handle_message(self, text: str) -> None:
        intent = detect_intent(text)
        if intent.kind == "pc_control":
            response = self._handle_pc_control(text)
        elif intent.kind == "web_search":
            response = self._handle_search(text)
        elif intent.kind == "realtime":
            response = self._handle_realtime(text)
        elif intent.kind == "writing":
            response = self.router.generate(text, need_reasoning=False)
        else:
            response = self.router.generate(text, need_reasoning=True)
        self.memory.add_session("assistant", response)
        self._append_chat("Assistant", response)
        self._maybe_store_memory(text, response)
        self._maybe_speak(response)

    def _handle_pc_control(self, text: str) -> str:
        lowered = text.lower()
        if lowered.startswith("open "):
            command = text[5:].strip()
            if command.startswith(("http://", "https://")) or command.startswith(("c:\\", "d:\\")):
                return open_path(command)
            return open_app(command)
        if lowered.startswith("close "):
            command = text[6:].strip()
            return close_app(command)
        if "volume" in lowered:
            level = self._extract_number(lowered)
            return set_volume(level if level is not None else 50)
        if "brightness" in lowered:
            level = self._extract_number(lowered)
            return set_brightness(level if level is not None else 70)
        if lowered.startswith("type "):
            text_to_type = text[5:].strip()
            return control_input("type", {"text": text_to_type})
        if lowered.startswith("press "):
            key = text[6:].strip()
            return control_input("press", {"key": key})
        if lowered.startswith("click "):
            coords = lowered.replace("click", "").strip().split()
            if len(coords) == 2 and all(item.isdigit() for item in coords):
                return control_input("click", {"x": int(coords[0]), "y": int(coords[1])})
            return "Please provide click coordinates like: click 120 300."
        return "Please specify an action like open, close, volume, brightness, type, press, or click."

    def _handle_search(self, text: str) -> str:
        query = text.split("search", 1)[-1].strip() if "search" in text.lower() else text
        results = search_web(query)
        answer = results.get("answer") or results.get("abstract") or "No summary available."
        return f"Search: {answer}"

    def _handle_realtime(self, text: str) -> str:
        lowered = text.lower()
        if "weather" in lowered:
            coords = [item for item in lowered.replace("weather", "").split() if self._is_number(item)]
            if len(coords) >= 2:
                data = weather(float(coords[0]), float(coords[1]))
                current = data.get("current_weather", {})
                temp = current.get("temperature")
                wind = current.get("windspeed")
                return f"Weather: {temp}°C, wind {wind} km/h."
            return "Share your city or provide coordinates like: weather 28.6 77.2"
        if "news" in lowered:
            query = lowered.replace("news", "").strip() or "latest"
            results = search_news(query)
            summary = results.get("abstract") or "No summary available."
            return f"News: {summary}"
        if "price" in lowered or "stock" in lowered:
            query = lowered.replace("price", "").replace("stock", "").strip()
            results = search_web(f"{query} price")
            answer = results.get("answer") or results.get("abstract") or "No summary available."
            return f"Price: {answer}"
        return "Tell me what real-time info you need (news, weather, price)."

    def _maybe_store_memory(self, user_text: str, response: str) -> None:
        lowered = user_text.lower()
        if "i like" in lowered or "my preference" in lowered:
            self.memory.remember_preference(user_text)
        if lowered.startswith(("open ", "close ", "type ", "press ", "click ")):
            self.memory.remember_command(user_text)
        if "write in" in lowered or "writing style" in lowered:
            self.memory.remember_style(user_text)

    def _maybe_speak(self, response: str) -> None:
        if not self.config.auto_speak:
            return
        try:
            self.speech.speak(response)
        except Exception:  # noqa: BLE001
            return

    def save_settings(self) -> None:
        self.config.llm_provider = self.provider_var.get() or "auto"
        self.config.ollama_host = self.ollama_host_var.get().strip() or self.config.ollama_host
        gemini_key = self.gemini_key_var.get().strip()
        self.config.gemini_api_key = gemini_key or None
        openrouter_key = self.openrouter_key_var.get().strip()
        self.config.openrouter_api_key = openrouter_key or None
        self.config.openrouter_model = self.openrouter_model_var.get().strip() or self.config.openrouter_model
        hf_key = self.hf_key_var.get().strip()
        self.config.hf_api_key = hf_key or None
        self.config.hf_model = self.hf_model_var.get().strip() or self.config.hf_model
        self.config.auto_speak = bool(self.auto_speak_var.get())
        messagebox.showinfo("Settings", "Settings saved for this session.")

    def _extract_number(self, text: str) -> int | None:
        parts = [item for item in text.split() if item.isdigit()]
        if not parts:
            return None
        return int(parts[0])

    def _is_number(self, value: str) -> bool:
        try:
            float(value)
        except ValueError:
            return False
        return True

    def _append_chat(self, role: str, message: str) -> None:
        def _insert() -> None:
            self.chat_log.insert(tk.END, f"{role}: {message}\n")
            self.chat_log.see(tk.END)

        self.root.after(0, _insert)

    def run(self) -> None:
        self.root.mainloop()
