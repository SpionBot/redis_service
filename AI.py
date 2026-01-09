import asyncio
import json
import logging
import re
import openai
from const import PROMPTS, game_array
from redis_client import save_game_clues
import os
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)


YANDEX_CLOUD_FOLDER = os.getenv("YANDEX_CLOUD_FOLDER")
YANDEX_CLOUD_API_KEY = os.getenv("YANDEX_CLOUD_API_KEY")
YANDEX_CLOUD_MODEL = os.getenv("YANDEX_CLOUD_MODEL")



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


def ask_llm(hero: str, promt: str, retries: int = 5) -> dict:
    client = openai.OpenAI(
        api_key=YANDEX_CLOUD_API_KEY,
        base_url="https://rest-assistant.api.cloud.yandex.net/v1",
        project=YANDEX_CLOUD_FOLDER,
        timeout=60
    )
    response = client.responses.create(
        model=f"gpt://{YANDEX_CLOUD_FOLDER}/{YANDEX_CLOUD_MODEL}",
        temperature=0.4,
        instructions=promt,
        input=hero,
    )
    text_output = response.output_text
    parsed_json = _extract_json_object(text_output)
    if parsed_json:
        return parsed_json
    logger.warning("Failed to extract JSON after %s retries", retries)
    return {}



async def generate_clue() -> None:
    while True:
        print('123')
        for game in game_array:
            heroes = game_array[game]
            for hero in heroes:
                prompt = PROMPTS[game]
                result = ask_llm(hero,prompt)
                print('RESULT:', result)
                if result:
                    save_game_clues(game, result)
                    logger.info("Generated and saved %s clues for game %s",game,prompt)
                else:
                    logger.warning("Empty result from LLM for game %s", game)
                await asyncio.sleep(2)
        await asyncio.sleep(604800)