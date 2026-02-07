from __future__ import annotations

import os
import subprocess
from typing import Any

from desktop_app.providers import is_module_available


def _load_pyautogui():
    if not is_module_available("pyautogui"):
        raise RuntimeError("pyautogui is not installed")
    return __import__("pyautogui")


def open_app(command: str) -> str:
    if os.name == "nt":
        subprocess.Popen(command, shell=True)
    else:
        subprocess.Popen(command, shell=True)
    return f"Opened: {command}"


def close_app(process_name: str) -> str:
    if os.name == "nt":
        subprocess.run(["taskkill", "/IM", process_name, "/F"], check=False)
    else:
        subprocess.run(["pkill", "-f", process_name], check=False)
    return f"Closed: {process_name}"


def control_input(action: str, payload: dict[str, Any]) -> str:
    pyautogui = _load_pyautogui()
    if action == "type":
        text = payload.get("text", "")
        pyautogui.write(text)
        return "Typed text."
    if action == "click":
        x = payload.get("x")
        y = payload.get("y")
        pyautogui.click(x, y)
        return "Clicked."
    if action == "press":
        key = payload.get("key", "")
        pyautogui.press(key)
        return "Pressed key."
    raise ValueError("Unsupported control action")
