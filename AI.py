import asyncio
import json
import logging
import math
import re

import requests
from const import PROMPTS, game_array
from redis_client import save_game_clues

logger = logging.getLogger(__name__)


def _extract_json_object(text: str) -> dict:
    if not text:
        return {}

    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    candidates = [match.group(1)] if match else []

    match = re.search(r"(\{.*\})", text, re.S)
    if match:
        candidates.append(match.group(1))

    candidates.append(text.strip())

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    logger.warning("LLM response did not contain a JSON object.")
    return {}


def ask_llm(api: str, promt: str) -> dict:
    if not api:
        logger.error("LLM API key is missing.")
        return {}

    headers = {
        "Authorization": f"Bearer {api}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mistralai/mistral-small-3.1-24b-instruct:free",
        "messages": [
            {"role": "system", "content": "Ты генератор подсказок для игры 'Шпион'"},
            {"role": "user", "content": promt},
        ],
        "temperature": 0.7,
    }

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("LLM request failed.")
        return {}

    try:
        body = response.json()
    except ValueError:
        logger.exception("LLM response was not JSON.")
        return {}

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        logger.warning("LLM response missing choices/content: %s", body)
        return {}

    return _extract_json_object(content)


async def generate_clue(api: str, game: str) -> None:
    while True:
        heroes = game_array[game]
        chunk_size = max(1, math.ceil(len(heroes) / 20))
        for idx, start in enumerate(range(0, len(heroes), chunk_size)):
            if idx >= 20:
                break
            chunk = heroes[start:start + chunk_size]
            prompt = PROMPTS[game].replace("[[]]", " ".join(map(str, chunk)))
            result = ask_llm(api, prompt)
            save_game_clues(game, result)
            logger.info("Generated and saved %s clues for game %s", len(result), game)
            asyncio.sleep(2)
        await asyncio.sleep(86400)
