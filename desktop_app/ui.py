from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from desktop_app.config import AppConfig
from desktop_app.intent import detect_intent
from desktop_app.memory import MemoryStore
from desktop_app.pc_control import close_app, open_app
from desktop_app.providers import LLMRouter
from desktop_app.realtime import search_web


class JarvisUI:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.router = LLMRouter(config)
        self.memory = MemoryStore(root_path="jarvis_memory")
        self.root = tk.Tk()
        self.root.title("Jarvis Desktop Assistant")

        self.chat_log = scrolledtext.ScrolledText(self.root, height=18, width=80)
        self.chat_log.pack(padx=12, pady=8)

        self.entry = tk.Entry(self.root, width=70)
        self.entry.pack(padx=12, pady=4, side=tk.LEFT)

        send_button = tk.Button(self.root, text="Send", command=self.on_send)
        send_button.pack(padx=4, pady=4, side=tk.LEFT)

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

    def _handle_message(self, text: str) -> None:
        intent = detect_intent(text)
        if intent.kind == "pc_control":
            response = self._handle_pc_control(text)
        elif intent.kind == "web_search":
            response = self._handle_search(text)
        else:
            response = self.router.generate(text)
        self.memory.add_session("assistant", response)
        self._append_chat("Assistant", response)

    def _handle_pc_control(self, text: str) -> str:
        lowered = text.lower()
        if lowered.startswith("open "):
            command = text[5:].strip()
            return open_app(command)
        if lowered.startswith("close "):
            command = text[6:].strip()
            return close_app(command)
        return "Please specify whether to open or close an app."

    def _handle_search(self, text: str) -> str:
        query = text.split("search", 1)[-1].strip() if "search" in text.lower() else text
        results = search_web(query)
        answer = results.get("answer") or results.get("abstract") or "No summary available."
        return f"Search: {answer}"

    def _append_chat(self, role: str, message: str) -> None:
        self.chat_log.insert(tk.END, f"{role}: {message}\n")
        self.chat_log.see(tk.END)

    def run(self) -> None:
        self.root.mainloop()
