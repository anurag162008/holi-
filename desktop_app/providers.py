from __future__ import annotations

import importlib.util
from typing import Any

import requests

from desktop_app.config import AppConfig, DEFAULT_SYSTEM_PROMPT


class LLMRouter:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def select_provider_chain(self, need_reasoning: bool, need_realtime: bool) -> list[str]:
        online = self._is_online()
        if not online:
            return ["ollama"]
        if need_realtime:
            return ["gemini", "openrouter", "huggingface", "ollama"]
        if need_reasoning:
            return ["ollama", "openrouter", "gemini", "huggingface"]
        return ["ollama", "gemini", "openrouter", "huggingface"]

    def generate(self, prompt: str, need_reasoning: bool = False, need_realtime: bool = False) -> str:
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
                response = provider(prompt, need_reasoning=need_reasoning, need_realtime=need_realtime)
                if response:
                    return response
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
        if last_error:
            raise RuntimeError(f"All providers failed: {last_error}") from last_error
        return "I'm offline right now. Please try again later."

    def _try_ollama(self, prompt: str, **_: Any) -> str | None:
        url = f"{self.config.ollama_host}/api/generate"
        payload = {"model": "llama3.1", "prompt": f"{DEFAULT_SYSTEM_PROMPT}\n{prompt}", "stream": False}
        response = requests.post(url, json=payload, timeout=20)
        if response.status_code >= 400:
            return None
        return response.json().get("response")

    def _try_gemini(self, prompt: str, **_: Any) -> str | None:
        if not self.config.gemini_api_key:
            return None
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        params = {"key": self.config.gemini_api_key}
        payload = {
            "contents": [{"parts": [{"text": f"{DEFAULT_SYSTEM_PROMPT}\n{prompt}"}]}],
            "generationConfig": {"temperature": 0.6},
        }
        response = requests.post(url, params=params, json=payload, timeout=20)
        if response.status_code >= 400:
            return None
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _try_openrouter(self, prompt: str, **_: Any) -> str | None:
        if not self.config.openrouter_api_key:
            return None
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": self.config.openrouter_model,
            "messages": [
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code >= 400:
            return None
        return response.json()["choices"][0]["message"]["content"]

    def _try_huggingface(self, prompt: str, **_: Any) -> str | None:
        if not self.config.hf_api_key:
            return None
        url = f"https://api-inference.huggingface.co/models/{self.config.hf_model}"
        headers = {"Authorization": f"Bearer {self.config.hf_api_key}"}
        payload = {"inputs": f"{DEFAULT_SYSTEM_PROMPT}\n{prompt}"}
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code >= 400:
            return None
        data = response.json()
        if isinstance(data, list) and data:
            return data[0].get("generated_text")
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]
        return None

    def _is_online(self) -> bool:
        try:
            response = requests.get("https://api.duckduckgo.com/", params={"q": "ping", "format": "json"}, timeout=3)
            return response.status_code < 400
        except requests.RequestException:
            return False


def is_module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def load_module(module_name: str) -> Any:
    if not is_module_available(module_name):
        raise RuntimeError(f"{module_name} is not installed")
    return __import__(module_name)
