from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import services.bot_manager as bm

router = APIRouter(prefix="/api/bots", tags=["bots"])


class RegisterBot(BaseModel):
    id: str
    name: str
    script_path: str
    description: str = ""


class UpdateConfig(BaseModel):
    config: dict


@router.get("/")
async def list_bots():
    return await bm.list_bots()


@router.post("/")
async def register_bot(body: RegisterBot):
    return await bm.register_bot(body.id, body.name, body.script_path, body.description)


@router.get("/{bot_id}")
async def get_bot(bot_id: str):
    bot = await bm.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, "Bot not found")
    return bot


@router.post("/{bot_id}/start")
async def start_bot(bot_id: str):
    try:
        return await bm.start_bot(bot_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except (RuntimeError, FileNotFoundError) as e:
        raise HTTPException(400, str(e))


@router.post("/{bot_id}/stop")
async def stop_bot(bot_id: str):
    try:
        return await bm.stop_bot(bot_id)
    except RuntimeError as e:
        raise HTTPException(400, str(e))


@router.put("/{bot_id}/config")
async def update_config(bot_id: str, body: UpdateConfig):
    bot = await bm.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, "Bot not found")
    return await bm.update_config(bot_id, body.config)


@router.get("/{bot_id}/logs")
async def get_logs(bot_id: str, lines: int = 100):
    bot = await bm.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, "Bot not found")
    logs = await bm.get_logs(bot_id, lines)
    return {"bot_id": bot_id, "logs": logs}


@router.delete("/{bot_id}")
async def delete_bot(bot_id: str):
    bot = await bm.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, "Bot not found")
    await bm.delete_bot(bot_id)
    return {"deleted": bot_id}
