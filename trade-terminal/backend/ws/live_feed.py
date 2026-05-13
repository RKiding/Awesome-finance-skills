"""
WebSocket live price feed.
Clients subscribe to symbols; server polls market data every N seconds and pushes updates.
"""
import asyncio
import json
from collections import defaultdict
from fastapi import WebSocket, WebSocketDisconnect
from services.market_data import get_quote

# symbol -> set of websockets
_subscribers: dict[str, set[WebSocket]] = defaultdict(set)
_all_sockets: set[WebSocket] = set()
_poll_task: asyncio.Task | None = None


async def handle_connection(ws: WebSocket):
    await ws.accept()
    _all_sockets.add(ws)
    subscribed: set[str] = set()

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            action = msg.get("action")
            symbol = str(msg.get("symbol", "")).upper()

            if action == "subscribe" and symbol:
                subscribed.add(symbol)
                _subscribers[symbol].add(ws)
                # Send immediately
                quote = await get_quote(symbol)
                await ws.send_json({"type": "quote", "data": quote})

            elif action == "unsubscribe" and symbol:
                subscribed.discard(symbol)
                _subscribers[symbol].discard(ws)

            elif action == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        _all_sockets.discard(ws)
        for sym in subscribed:
            _subscribers[sym].discard(ws)


async def start_price_poller(interval: int = 5):
    """Background task: poll all subscribed symbols every `interval` seconds."""
    global _poll_task

    async def _loop():
        while True:
            await asyncio.sleep(interval)
            active_symbols = [s for s, sockets in _subscribers.items() if sockets]
            if not active_symbols:
                continue
            quotes = await asyncio.gather(
                *[get_quote(s) for s in active_symbols],
                return_exceptions=True
            )
            for symbol, quote in zip(active_symbols, quotes):
                if isinstance(quote, Exception):
                    continue
                dead = set()
                for ws in list(_subscribers[symbol]):
                    try:
                        await ws.send_json({"type": "quote", "data": quote})
                    except Exception:
                        dead.add(ws)
                for ws in dead:
                    _subscribers[symbol].discard(ws)
                    _all_sockets.discard(ws)

    _poll_task = asyncio.create_task(_loop())
