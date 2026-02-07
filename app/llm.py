from __future__ import annotations

from typing import Any
import os

import requests

DEFAULT_SYSTEM_PROMPT = (
    "You are Divya, a polite, helpful AI assistant with a warm, friendly tone. "
    "You are a Jarvis-style system controller for the user's own PC. "
    "Always ask for confirmation before any risky action."
)


class LLMRouter:
    def __init__(self) -> None:
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.llm_provider = os.getenv("LLM_PROVIDER", "auto")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.hf_api_key = os.getenv("HF_API_KEY")
        self.hf_model = os.getenv("HF_MODEL", "google/flan-t5-large")

    def select_provider_chain(self, need_reasoning: bool, need_realtime: bool) -> list[str]:
        if self.llm_provider and self.llm_provider != "auto":
            return [self.llm_provider]
        online = self._is_online()
        if not online:
            return ["ollama"]
        if need_realtime:
            return ["gemini", "openrouter", "huggingface", "ollama"]
        if need_reasoning:
            return ["ollama", "openrouter", "gemini", "huggingface"]
        return ["ollama", "gemini", "openrouter", "huggingface"]

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        need_reasoning: bool = False,
        need_realtime: bool = False,
    ) -> str:
        provider_map = {
            "ollama": self._try_ollama,
            "gemini": self._try_gemini,
            "openrouter": self._try_openrouter,
            "huggingface": self._try_huggingface,
        }
        provider_chain = [provider_map[key] for key in self.select_provider_chain(need_reasoning, need_realtime)]
        last_error = None
        for provider in provider_chain:
            try:
                response = provider(prompt, system_prompt=system_prompt)
                if response:
                    return response
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
        if last_error:
            return (
                "I'm having trouble reaching the AI provider right now. "
                "Please check your provider settings or try again later."
            )
        return "I'm offline right now. Please try again later."

    def _try_ollama(self, prompt: str, *, system_prompt: str | None = None) -> str | None:
        url = f"{self.ollama_host}/api/generate"
        prompt_text = self._build_prompt(prompt, system_prompt)
        payload = {"model": "llama3.1", "prompt": prompt_text, "stream": False}
        response = requests.post(url, json=payload, timeout=20)
        if response.status_code >= 400:
            return None
        return response.json().get("response")

    def _try_gemini(self, prompt: str, *, system_prompt: str | None = None) -> str | None:
        if not self.gemini_api_key:
            return None
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        params = {"key": self.gemini_api_key}
        payload = {
            "contents": [{"parts": [{"text": self._build_prompt(prompt, system_prompt)}]}],
            "generationConfig": {"temperature": 0.6},
        }
        response = requests.post(url, params=params, json=payload, timeout=20)
        if response.status_code >= 400:
            return None
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _try_openrouter(self, prompt: str, *, system_prompt: str | None = None) -> str | None:
        if not self.openrouter_api_key:
            return None
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": self.openrouter_model,
            "messages": [
                {"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code >= 400:
            return None
        return response.json()["choices"][0]["message"]["content"]

    def _try_huggingface(self, prompt: str, *, system_prompt: str | None = None) -> str | None:
        if not self.hf_api_key:
            return None
        url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
        headers = {"Authorization": f"Bearer {self.hf_api_key}"}
        payload = {"inputs": self._build_prompt(prompt, system_prompt)}
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code >= 400:
            return None
        data = response.json()
        if isinstance(data, list) and data:
            return data[0].get("generated_text")
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]
        return None

    def _build_prompt(self, prompt: str, system_prompt: str | None) -> str:
        base = system_prompt or DEFAULT_SYSTEM_PROMPT
        return f"{base}\n{prompt}"

    def _is_online(self) -> bool:
        try:
            response = requests.get("https://api.duckduckgo.com/", params={"q": "ping", "format": "json"}, timeout=3)
            return response.status_code < 400
        except requests.RequestException:
            return False
