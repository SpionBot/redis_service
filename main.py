from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import logging,asyncio,os
from typing import Any, Dict
from redis_client import get_game_clues
from AI import generate_clue
from redis_client import r
logger = logging.getLogger(__name__)

async def lifespan(app: FastAPI):
    task_1 = asyncio.create_task(generate_clue())
    yield
    task_1.cancel()
    try:
        await task_1
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
    print(len(get_game_clues(data.game)))
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

