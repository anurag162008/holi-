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
    if action == "hotkey":
        keys = payload.get("keys", [])
        pyautogui.hotkey(*keys)
        return "Pressed hotkey."
    raise ValueError("Unsupported control action")


def set_volume(level: int) -> str:
    safe_level = max(0, min(100, level))
    if os.name == "nt":
        for _ in range(50):
            subprocess.run(["nircmd.exe", "changesysvolume", "-2000"], check=False)
        steps = int(safe_level / 2)
        for _ in range(steps):
            subprocess.run(["nircmd.exe", "changesysvolume", "2000"], check=False)
        return f"Volume set to {safe_level}%."
    return "Volume control is available on Windows with nircmd.exe."


def set_brightness(level: int) -> str:
    safe_level = max(0, min(100, level))
    if os.name == "nt":
        subprocess.run(
            [
                "powershell",
                "-Command",
                (
                    "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                    f".WmiSetBrightness(1,{safe_level})"
                ),
            ],
            check=False,
        )
        return f"Brightness set to {safe_level}%."
    return "Brightness control is available on Windows."


def open_path(path: str) -> str:
    expanded = os.path.expanduser(path)
    if os.name == "nt":
        subprocess.Popen(["explorer", expanded], shell=False)
    else:
        subprocess.Popen(["xdg-open", expanded], shell=False)
    return f"Opened path: {expanded}"
