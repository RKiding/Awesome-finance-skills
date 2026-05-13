from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.fundamental_data import get_full_fundamental, get_macro_snapshot
from services.ai_analyst import analyze_fundamental, analyze_macro, chat_analyst

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    symbol: str
    question: str = ""


class MacroRequest(BaseModel):
    question: str = ""


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    symbol: Optional[str] = None


@router.post("/fundamental")
async def fundamental_analysis(req: AnalysisRequest):
    data = await get_full_fundamental(req.symbol.upper())
    result = await analyze_fundamental(req.symbol.upper(), data, req.question)
    result["raw_data"] = data
    return result


@router.get("/fundamental/{symbol}")
async def fundamental_analysis_get(symbol: str, question: str = ""):
    data = await get_full_fundamental(symbol.upper())
    result = await analyze_fundamental(symbol.upper(), data, question)
    result["raw_data"] = data
    return result


@router.post("/macro")
async def macro_analysis(req: MacroRequest):
    data = await get_macro_snapshot()
    if "error" in data:
        raise HTTPException(400, data["error"])
    return await analyze_macro(data, req.question)


@router.get("/macro")
async def macro_analysis_get(question: str = ""):
    data = await get_macro_snapshot()
    if "error" in data:
        raise HTTPException(400, data["error"])
    return await analyze_macro(data, question)


@router.post("/chat")
async def analyst_chat(req: ChatRequest):
    context = None
    if req.symbol:
        context = await get_full_fundamental(req.symbol.upper())
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    reply = await chat_analyst(messages, context)
    return {"reply": reply}
