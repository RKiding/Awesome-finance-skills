from fastapi import APIRouter, Query
from services.market_data import get_quote, get_ohlcv, search_symbols

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/quote/{symbol}")
async def quote(symbol: str):
    return await get_quote(symbol.upper())


@router.get("/ohlcv/{symbol}")
async def ohlcv(
    symbol: str,
    interval: str = Query("1day", description="1min,5min,15min,1h,4h,1day,1week"),
    limit: int = Query(90, ge=10, le=500),
):
    data = await get_ohlcv(symbol.upper(), interval, limit)
    return {"symbol": symbol.upper(), "interval": interval, "data": data}


@router.get("/search")
async def search(q: str = Query(..., min_length=1)):
    return await search_symbols(q)


@router.get("/quotes")
async def multi_quote(symbols: str = Query(..., description="Comma-separated symbols")):
    import asyncio
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    results = await asyncio.gather(*[get_quote(s) for s in syms])
    return {r["symbol"]: r for r in results}
