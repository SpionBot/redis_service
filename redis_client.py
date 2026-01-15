import json
import os
import logging
from typing import Dict, Any

import redis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
else:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

_HASH_PREFIX = "clues"


def _game_key(game: str) -> str:
    """Build a stable Redis hash key for a given game."""
    return f"{_HASH_PREFIX}:{game.lower()}"


def save_game_clues(game: str, clues: Dict[str, Any]) -> None:
    """
    Persist hero clues for a game into a Redis hash.

    Each hash field is the hero name, and the value is a JSON blob with
    difficulty buckets (hard/medium/easy). Using a hash keeps lookups O(1)
    and avoids collisions across games.
    """
    if not clues:
        return

    hash_key = _game_key(game)
    pipe = r.pipeline()
    for hero, payload in clues.items():
        pipe.hset(hash_key, hero, json.dumps(payload))
    pipe.execute()
    logger.info("Saved %s hero clues for game %s into %s", len(clues), game, hash_key)


def get_game_clues(game: str) -> Dict[str, Any]:
    """
    Fetch all hero clues for a given game as a dict keyed by hero name.

    Returned format:
    {
        "HeroName": {"hard": [...], "medium": [...], "easy": [...]},
        ...
    }
    """
    raw = r.hgetall(_game_key(game))
    parsed = {}
    for hero, payload in raw.items():
        try:
            parsed[hero] = json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("Failed to decode payload for hero %s in game %s", hero, game)
    return parsed
