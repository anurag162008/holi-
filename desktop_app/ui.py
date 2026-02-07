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
        try:
            self.speech.speak(response)
        except Exception:  # noqa: BLE001
            return

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
