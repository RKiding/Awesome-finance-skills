"""
Fundamental analysis data.
Sources: Finnhub (free) + SEC EDGAR (official, free) + FRED (macro, free) + Alpha Vantage (free tier)
"""
import httpx
from typing import Optional
from config import FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY, FRED_API_KEY

_client = httpx.AsyncClient(timeout=20)


# ── Finnhub Fundamentals ──────────────────────────────────────────────────────

async def get_company_profile(symbol: str) -> Optional[dict]:
    if not FINNHUB_API_KEY:
        return None
    try:
        r = await _client.get(
            "https://finnhub.io/api/v1/stock/profile2",
            params={"symbol": symbol, "token": FINNHUB_API_KEY}
        )
        d = r.json()
        return d if d.get("name") else None
    except Exception:
        return None


async def get_basic_financials(symbol: str) -> Optional[dict]:
    if not FINNHUB_API_KEY:
        return None
    try:
        r = await _client.get(
            "https://finnhub.io/api/v1/stock/metric",
            params={"symbol": symbol, "metric": "all", "token": FINNHUB_API_KEY}
        )
        return r.json()
    except Exception:
        return None


async def get_earnings(symbol: str) -> Optional[list]:
    if not FINNHUB_API_KEY:
        return None
    try:
        r = await _client.get(
            "https://finnhub.io/api/v1/stock/earnings",
            params={"symbol": symbol, "token": FINNHUB_API_KEY}
        )
        return r.json()
    except Exception:
        return None


async def get_news_sentiment(symbol: str, days: int = 7) -> Optional[dict]:
    if not FINNHUB_API_KEY:
        return None
    from datetime import datetime, timedelta
    to = datetime.utcnow().strftime("%Y-%m-%d")
    frm = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        r = await _client.get(
            "https://finnhub.io/api/v1/news-sentiment",
            params={"symbol": symbol, "token": FINNHUB_API_KEY}
        )
        return r.json()
    except Exception:
        return None


async def get_company_news(symbol: str, days: int = 7) -> list:
    if not FINNHUB_API_KEY:
        return []
    from datetime import datetime, timedelta
    to = datetime.utcnow().strftime("%Y-%m-%d")
    frm = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        r = await _client.get(
            "https://finnhub.io/api/v1/company-news",
            params={"symbol": symbol, "from": frm, "to": to, "token": FINNHUB_API_KEY}
        )
        news = r.json()
        return news[:20] if isinstance(news, list) else []
    except Exception:
        return []


async def get_peers(symbol: str) -> list:
    if not FINNHUB_API_KEY:
        return []
    try:
        r = await _client.get(
            "https://finnhub.io/api/v1/stock/peers",
            params={"symbol": symbol, "token": FINNHUB_API_KEY}
        )
        return r.json() if isinstance(r.json(), list) else []
    except Exception:
        return []


# ── SEC EDGAR (official US gov API, completely free) ─────────────────────────

async def get_sec_filings(ticker: str, form_type: str = "10-K", count: int = 5) -> list:
    """Get recent SEC filings for a US company."""
    try:
        # First get CIK from ticker
        r = await _client.get(
            "https://efts.sec.gov/LATEST/search-index?q=%22{}%22&dateRange=custom&startdt=2020-01-01&forms={}".format(
                ticker, form_type
            ),
            headers={"User-Agent": "TradeTerminal personal@example.com"}
        )
        # Use company search endpoint
        r2 = await _client.get(
            f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&forms={form_type}",
            headers={"User-Agent": "TradeTerminal personal@example.com"}
        )
        data = r2.json()
        hits = data.get("hits", {}).get("hits", [])
        return [
            {
                "form": h["_source"].get("form_type"),
                "filed": h["_source"].get("file_date"),
                "description": h["_source"].get("display_names", [{}])[0].get("name", ""),
                "url": f"https://www.sec.gov/Archives/edgar/data/{h['_source'].get('entity_id')}/{h['_source'].get('file_num', '')}",
            }
            for h in hits[:count]
        ]
    except Exception:
        return []


# ── FRED Macro Data (Federal Reserve, completely free) ────────────────────────

FRED_SERIES = {
    "gdp": "GDP",
    "inflation": "CPIAUCSL",
    "unemployment": "UNRATE",
    "fed_rate": "FEDFUNDS",
    "10y_yield": "DGS10",
    "2y_yield": "DGS2",
    "vix": "VIXCLS",
    "sp500": "SP500",
    "dollar_index": "DTWEXBGS",
    "oil_wti": "DCOILWTICO",
}


async def get_fred_series(series_id: str, limit: int = 12) -> Optional[dict]:
    if not FRED_API_KEY:
        return None
    try:
        r = await _client.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id": series_id,
                "api_key": FRED_API_KEY,
                "file_type": "json",
                "sort_order": "desc",
                "limit": limit,
            }
        )
        data = r.json()
        obs = data.get("observations", [])
        return {
            "series_id": series_id,
            "observations": [
                {"date": o["date"], "value": o["value"]}
                for o in reversed(obs)
                if o["value"] != "."
            ]
        }
    except Exception:
        return None


async def get_macro_snapshot() -> dict:
    """Get key macro indicators in one call."""
    if not FRED_API_KEY:
        return {"error": "FRED_API_KEY not set"}

    import asyncio
    tasks = {
        name: get_fred_series(series_id, limit=3)
        for name, series_id in FRED_SERIES.items()
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    return {
        name: (r if not isinstance(r, Exception) else None)
        for name, r in zip(tasks.keys(), results)
    }


# ── Alpha Vantage Income/Balance Sheet ───────────────────────────────────────

async def get_income_statement(symbol: str) -> Optional[dict]:
    if not ALPHA_VANTAGE_API_KEY:
        return None
    try:
        r = await _client.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "INCOME_STATEMENT",
                "symbol": symbol,
                "apikey": ALPHA_VANTAGE_API_KEY,
            }
        )
        data = r.json()
        reports = data.get("annualReports", [])[:4]
        return {"symbol": symbol, "annual_reports": reports}
    except Exception:
        return None


async def get_overview(symbol: str) -> Optional[dict]:
    if not ALPHA_VANTAGE_API_KEY:
        return None
    try:
        r = await _client.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "OVERVIEW",
                "symbol": symbol,
                "apikey": ALPHA_VANTAGE_API_KEY,
            }
        )
        data = r.json()
        return data if data.get("Symbol") else None
    except Exception:
        return None


# ── Unified fundamental bundle ────────────────────────────────────────────────

async def get_full_fundamental(symbol: str) -> dict:
    import asyncio
    profile, metrics, earnings, sentiment, news, overview = await asyncio.gather(
        get_company_profile(symbol),
        get_basic_financials(symbol),
        get_earnings(symbol),
        get_news_sentiment(symbol),
        get_company_news(symbol, days=3),
        get_overview(symbol),
        return_exceptions=True
    )
    return {
        "symbol": symbol,
        "profile": profile if not isinstance(profile, Exception) else None,
        "metrics": metrics if not isinstance(metrics, Exception) else None,
        "earnings": earnings if not isinstance(earnings, Exception) else None,
        "sentiment": sentiment if not isinstance(sentiment, Exception) else None,
        "news": news if not isinstance(news, Exception) else [],
        "overview": overview if not isinstance(overview, Exception) else None,
    }
