import hashlib
import json
import logging
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from app.config import (
    HTTP_USER_AGENT,
    REQUEST_TIMEOUT,
    SOURCES_PATH,
    UPDATE_STATE_PATH,
    WIKTIONARY_API_URL,
    WIKTIONARY_PAGE_TITLE,
    WIKTIONARY_URL,
)
from app.services.phrase_repository import load_phrases, save_phrases
from app.utils.text import is_valid_two_word_phrase, normalize_phrase_text

logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_update_state() -> dict:
    if not UPDATE_STATE_PATH.exists():
        return {}

    try:
        with UPDATE_STATE_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_update_state(data: dict) -> None:
    UPDATE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with UPDATE_STATE_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def save_sources(total_count: int) -> None:
    payload = {
        "updated_at": utc_now_iso(),
        "sources": [
            {
                "name": "Русский Викисловарь",
                "type": "open_source_web",
                "url": WIKTIONARY_URL,
                "note": "Используется открытый список фразеологизмов.",
            }
        ],
        "total_phrases": total_count,
    }
    SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SOURCES_PATH.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def fetch_wiktionary_phrases() -> tuple[list[str], str]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": HTTP_USER_AGENT,
            "Accept": "application/json, text/html;q=0.9,*/*;q=0.8",
        }
    )

    response = session.get(
        WIKTIONARY_API_URL,
        params={
            "action": "parse",
            "page": WIKTIONARY_PAGE_TITLE,
            "prop": "text",
            "format": "json",
            "formatversion": "2",
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    payload = response.json()
    html = payload["parse"]["text"]

    soup = BeautifulSoup(html, "html.parser")
    phrases: set[str] = set()

    for link in soup.select("a"):
        text = normalize_phrase_text(link.get_text(" ", strip=True))
        if is_valid_two_word_phrase(text):
            phrases.add(text)

    content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
    return sorted(phrases), content_hash


def update_phrases(force: bool = False) -> dict:
    state = load_update_state()

    try:
        remote_phrases, remote_hash = fetch_wiktionary_phrases()
    except Exception as error:
        logger.warning("Не удалось обновить список фраз: %s", error)
        state["last_checked_at"] = utc_now_iso()
        state["last_error"] = str(error)
        save_update_state(state)

        current_count = len(load_phrases())
        return {
            "updated": False,
            "reason": "fetch_failed",
            "count": current_count,
        }

    current_phrases = load_phrases()
    current_hash = state.get("source_hash", "")

    if not force and remote_hash == current_hash:
        state["last_checked_at"] = utc_now_iso()
        state["last_error"] = ""
        save_update_state(state)
        save_sources(len(current_phrases))
        return {
            "updated": False,
            "reason": "no_changes",
            "count": len(current_phrases),
        }

    merged = sorted(set(current_phrases) | set(remote_phrases))
    save_phrases(merged)
    save_sources(len(merged))

    now = utc_now_iso()
    state["last_checked_at"] = now
    state["last_updated_at"] = now
    state["source_hash"] = remote_hash
    state["last_error"] = ""
    save_update_state(state)

    return {
        "updated": True,
        "reason": "changed" if current_hash else "initial_build",
        "count": len(merged),
    }
