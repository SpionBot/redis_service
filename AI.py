import asyncio
import json
import logging
import math
import re

from google import genai

from const import PROMPTS, game_array
from redis_client import save_game_clues

logger = logging.getLogger(__name__)


def ask_llm(api: str, promt: str) -> dict:
    client = genai.Client(api_key=api)

    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=promt,
    )
    raw = response.text
    match = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.S)
    json_str = match.group(1)
    data = json.loads(json_str)
    return data


async def generate_clue(api: str, game: str) -> None:
    await asyncio.sleep(60)
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
        await asyncio.sleep(86400)
