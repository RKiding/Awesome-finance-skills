"""
Market data aggregator.
Priority: Twelve Data (stocks/crypto/forex) → Finnhub (US equities) → Binance (crypto) → yfinance (fallback)
All APIs are free tier, personal use legal.
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional
from config import TWELVE_DATA_API_KEY, FINNHUB_API_KEY

_client = httpx.AsyncClient(timeout=15)


# ── Twelve Data ──────────────────────────────────────────────────────────────

async def get_quote_twelve(symbol: str) -> Optional[dict]:
    if not TWELVE_DATA_API_KEY:
        return None
    try:
        r = await _client.get(
            "https://api.twelvedata.com/quote",
            params={"symbol": symbol, "apikey": TWELVE_DATA_API_KEY}
        )
        data = r.json()
        if data.get("status") == "error":
            return None
        return {
            "symbol": symbol,
            "price": float(data.get("close", 0)),
            "open": float(data.get("open", 0)),
            "high": float(data.get("high", 0)),
            "low": float(data.get("low", 0)),
            "volume": int(data.get("volume", 0)),
            "change": float(data.get("change", 0)),
            "change_pct": float(data.get("percent_change", 0)),
            "name": data.get("name", symbol),
            "exchange": data.get("exchange", ""),
            "currency": data.get("currency", "USD"),
            "source": "twelve_data",
        }
    except Exception:
        return None


async def get_ohlcv_twelve(
    symbol: str,
    interval: str = "1day",
    outputsize: int = 90
) -> Optional[list]:
    """interval: 1min,5min,15min,30min,1h,2h,4h,1day,1week,1month"""
    if not TWELVE_DATA_API_KEY:
        return None
    try:
        r = await _client.get(
            "https://api.twelvedata.com/time_series",
            params={
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": TWELVE_DATA_API_KEY,
            }
        )
        data = r.json()
        if data.get("status") == "error":
            return None
        values = data.get("values", [])
        return [
            {
                "time": v["datetime"],
                "open": float(v["open"]),
                "high": float(v["high"]),
                "low": float(v["low"]),
                "close": float(v["close"]),
                "volume": int(v.get("volume", 0)),
            }
            for v in reversed(values)
        ]
    except Exception:
        return None


# ── Finnhub ───────────────────────────────────────────────────────────────────

async def get_quote_finnhub(symbol: str) -> Optional[dict]:
    if not FINNHUB_API_KEY:
        return None
    try:
        r = await _client.get(
            "https://finnhub.io/api/v1/quote",
            params={"symbol": symbol, "token": FINNHUB_API_KEY}
        )
        d = r.json()
        if not d.get("c"):
            return None
        return {
            "symbol": symbol,
            "price": d["c"],
            "open": d["o"],
            "high": d["h"],
            "low": d["l"],
            "prev_close": d["pc"],
            "change": d["c"] - d["pc"],
            "change_pct": ((d["c"] - d["pc"]) / d["pc"] * 100) if d["pc"] else 0,
            "source": "finnhub",
        }
    except Exception:
        return None


# ── Binance (crypto, no key needed) ──────────────────────────────────────────

async def get_quote_binance(symbol: str) -> Optional[dict]:
    try:
        r = await _client.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbol": symbol.upper()}
        )
        d = r.json()
        if "code" in d:
            return None
        return {
            "symbol": symbol,
            "price": float(d["lastPrice"]),
            "open": float(d["openPrice"]),
            "high": float(d["highPrice"]),
            "low": float(d["lowPrice"]),
            "volume": float(d["volume"]),
            "change": float(d["priceChange"]),
            "change_pct": float(d["priceChangePercent"]),
            "source": "binance",
        }
    except Exception:
        return None


async def get_ohlcv_binance(
    symbol: str,
    interval: str = "1d",
    limit: int = 90
) -> Optional[list]:
    """interval: 1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M"""
    try:
        r = await _client.get(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": symbol.upper(), "interval": interval, "limit": limit}
        )
        rows = r.json()
        if not isinstance(rows, list):
            return None
        return [
            {
                "time": datetime.utcfromtimestamp(row[0] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
            }
            for row in rows
        ]
    except Exception:
        return None


# ── yfinance fallback ─────────────────────────────────────────────────────────

async def get_quote_yfinance(symbol: str) -> Optional[dict]:
    try:
        import yfinance as yf
        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, lambda: yf.Ticker(symbol))
        info = await loop.run_in_executor(None, lambda: ticker.fast_info)
        price = getattr(info, "last_price", None) or getattr(info, "regularMarketPrice", None)
        if not price:
            return None
        return {
            "symbol": symbol,
            "price": float(price),
            "source": "yfinance",
        }
    except Exception:
        return None


# ── Unified API ───────────────────────────────────────────────────────────────

_CRYPTO_PAIRS = {"BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"}

def _is_crypto_binance(symbol: str) -> bool:
    s = symbol.upper()
    return s in _CRYPTO_PAIRS or s.endswith("USDT") or s.endswith("BTC")


async def get_quote(symbol: str) -> dict:
    if _is_crypto_binance(symbol):
        result = await get_quote_binance(symbol)
        if result:
            return result

    result = await get_quote_twelve(symbol)
    if result:
        return result

    result = await get_quote_finnhub(symbol)
    if result:
        return result

    result = await get_quote_yfinance(symbol)
    if result:
        return result

    return {"symbol": symbol, "error": "No data found", "price": None}


async def get_ohlcv(symbol: str, interval: str = "1day", limit: int = 90) -> list:
    if _is_crypto_binance(symbol):
        # Map interval to Binance format
        mapping = {"1day": "1d", "1h": "1h", "4h": "4h", "15min": "15m", "5min": "5m", "1week": "1w"}
        bi = mapping.get(interval, "1d")
        result = await get_ohlcv_binance(symbol, bi, limit)
        if result:
            return result

    result = await get_ohlcv_twelve(symbol, interval, limit)
    if result:
        return result

    return []


async def search_symbols(query: str) -> list:
    results = []

    if TWELVE_DATA_API_KEY:
        try:
            r = await _client.get(
                "https://api.twelvedata.com/symbol_search",
                params={"symbol": query, "apikey": TWELVE_DATA_API_KEY}
            )
            data = r.json()
            for item in data.get("data", [])[:10]:
                results.append({
                    "symbol": item.get("symbol"),
                    "name": item.get("instrument_name"),
                    "exchange": item.get("exchange"),
                    "type": item.get("instrument_type"),
                })
        except Exception:
            pass

    if FINNHUB_API_KEY and len(results) < 5:
        try:
            r = await _client.get(
                "https://finnhub.io/api/v1/search",
                params={"q": query, "token": FINNHUB_API_KEY}
            )
            for item in r.json().get("result", [])[:5]:
                results.append({
                    "symbol": item.get("symbol"),
                    "name": item.get("description"),
                    "exchange": item.get("primaryExchange"),
                    "type": item.get("type"),
                })
        except Exception:
            pass

    return results
