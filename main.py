from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import logging,asyncio,os
from typing import Any, Dict
from redis_client import get_game_clues
from AI import generate_clue
from redis_client import r
load_dotenv()
logger = logging.getLogger(__name__)
AI_KEY_1 = os.getenv("AI_KEY_1")
AI_KEY_2 = os.getenv("AI_KEY_2")

async def lifespan(app: FastAPI):
    task_1 = asyncio.create_task(generate_clue(AI_KEY_1,"dota2"))
    task_2 = asyncio.create_task(generate_clue(AI_KEY_1, "clashroyale"))
    yield
    task_1.cancel()
    task_2.cancel()
    try:
        await task_1
        await task_2
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

class user(BaseModel):
    password: str
    game : str

HASH = os.getenv("HASH")
@app.post("/check_connection")
async def check_connection(data : user) -> Dict[str, Any]:
    if data.password != HASH:
        return {'status': False}
    return {'result': get_game_clues(data.game)}
@app.get("/check_connection")
async def check_connection() -> dict:
    try:
        r.ping()
        logger.info("✅ Redis connected successfully!")
        return {'status': 'ok'}
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return {'status': 'error'}

