from __future__ import annotations

from typing import Any

import requests


def search_web(query: str) -> dict[str, Any]:
    response = requests.get(
        "https://api.duckduckgo.com/",
        params={"q": query, "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "heading": data.get("Heading"),
        "abstract": data.get("Abstract"),
        "answer": data.get("Answer"),
        "related": [item.get("Text") for item in data.get("RelatedTopics", []) if item.get("Text")],
    }


def search_news(query: str) -> dict[str, Any]:
    response = requests.get(
        "https://api.duckduckgo.com/",
        params={"q": f"{query} news", "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "heading": data.get("Heading"),
        "abstract": data.get("Abstract"),
        "related": [item.get("Text") for item in data.get("RelatedTopics", []) if item.get("Text")],
    }


def weather(lat: float, lon: float) -> dict[str, Any]:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current_weather=true"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
