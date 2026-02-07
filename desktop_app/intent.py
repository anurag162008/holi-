from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Intent:
    kind: str
    payload: str


def detect_intent(text: str) -> Intent:
    lowered = text.lower().strip()
    if lowered.startswith("open ") or lowered.startswith("close "):
        return Intent(kind="pc_control", payload=text)
    if "search" in lowered or lowered.startswith("find "):
        return Intent(kind="web_search", payload=text)
    if any(keyword in lowered for keyword in ("volume", "brightness", "screenshot", "type ", "press ", "click ")):
        return Intent(kind="pc_control", payload=text)
    if "shayari" in lowered or "poem" in lowered:
        return Intent(kind="writing", payload=text)
    if "weather" in lowered or "news" in lowered or "price" in lowered or "stock" in lowered:
        return Intent(kind="realtime", payload=text)
    return Intent(kind="general", payload=text)
