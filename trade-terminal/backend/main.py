import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config import FRONTEND_URL
from routers import bots, market, analysis
from ws.live_feed import handle_connection, start_price_poller
from services.bot_manager import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await start_price_poller(interval=5)
    yield


app = FastAPI(title="Trade Terminal API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bots.router)
app.include_router(market.router)
app.include_router(analysis.router)


@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    await handle_connection(ws)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve Next.js static build if it exists
_static = Path(__file__).parent.parent / "frontend" / "out"
if _static.exists():
    app.mount("/", StaticFiles(directory=str(_static), html=True), name="frontend")
