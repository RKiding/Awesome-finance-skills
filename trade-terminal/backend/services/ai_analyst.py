"""
Claude-powered fundamental analysis interpreter.
Takes raw data → structured AI commentary.
"""
import anthropic
import json
from config import ANTHROPIC_API_KEY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a senior equity research analyst with deep expertise in fundamental analysis, macroeconomics, and quantitative finance.

Your job is to interpret financial data and provide clear, actionable insights. Be concise and direct. Structure your analysis in clear sections. Use bullet points. Flag risks prominently. Do not use fluff or filler phrases.

Respond in the same language the user uses (Turkish or English)."""


async def analyze_fundamental(symbol: str, data: dict, user_question: str = "") -> dict:
    """
    Takes fundamental data bundle and produces structured AI analysis.
    """
    import asyncio

    question = user_question or f"Provide a comprehensive fundamental analysis of {symbol}."

    # Build context from data
    context_parts = []

    if data.get("profile"):
        p = data["profile"]
        context_parts.append(f"**Company:** {p.get('name')} ({symbol})\n"
                             f"Industry: {p.get('finnhubIndustry')} | Country: {p.get('country')}\n"
                             f"Market Cap: {p.get('marketCapitalization')}M | Exchange: {p.get('exchange')}")

    if data.get("overview"):
        ov = data["overview"]
        context_parts.append(
            f"**Key Metrics (Alpha Vantage):**\n"
            f"P/E: {ov.get('PERatio')} | P/B: {ov.get('PriceToBookRatio')} | EPS: {ov.get('EPS')}\n"
            f"Revenue TTM: {ov.get('RevenueTTM')} | Profit Margin: {ov.get('ProfitMargin')}\n"
            f"52W High: {ov.get('52WeekHigh')} | 52W Low: {ov.get('52WeekLow')}\n"
            f"Dividend Yield: {ov.get('DividendYield')} | Beta: {ov.get('Beta')}\n"
            f"Analyst Target: {ov.get('AnalystTargetPrice')}"
        )

    if data.get("metrics") and data["metrics"].get("metric"):
        m = data["metrics"]["metric"]
        selected = {
            k: m[k] for k in [
                "peNormalizedAnnual", "pbAnnual", "psAnnual", "roeAnnual",
                "roaAnnual", "debtEquityAnnual", "currentRatioAnnual",
                "revenueGrowth3Y", "epsGrowth3Y", "netMarginAnnual"
            ] if k in m
        }
        context_parts.append(f"**Finnhub Metrics:**\n{json.dumps(selected, indent=2)}")

    if data.get("earnings") and isinstance(data["earnings"], list):
        recent = data["earnings"][:4]
        lines = [f"{e.get('period')}: EPS actual={e.get('actual')} estimate={e.get('estimate')} surprise={e.get('surprise')}" for e in recent]
        context_parts.append("**Earnings History (last 4Q):**\n" + "\n".join(lines))

    if data.get("sentiment"):
        s = data["sentiment"]
        context_parts.append(
            f"**News Sentiment:**\n"
            f"Buzz score: {s.get('buzz', {}).get('buzz')}\n"
            f"Sentiment score: {s.get('sentiment', {}).get('bearishPercent')} bear / {s.get('sentiment', {}).get('bullishPercent')} bull"
        )

    if data.get("news"):
        headlines = [n.get("headline", "") for n in data["news"][:5]]
        context_parts.append("**Recent Headlines:**\n" + "\n".join(f"• {h}" for h in headlines))

    context = "\n\n".join(context_parts)

    prompt = f"""## Data for {symbol}

{context}

---

{question}

Structure your response as:
1. **Summary** (2-3 sentences)
2. **Bull Case** (3 bullet points)
3. **Bear Case** (3 bullet points)
4. **Key Metrics Assessment**
5. **Verdict** (Buy / Hold / Sell with brief rationale)"""

    loop = __import__("asyncio").get_event_loop()

    def _call():
        msg = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text

    text = await loop.run_in_executor(None, _call)
    return {"symbol": symbol, "analysis": text, "question": question}


async def analyze_macro(macro_data: dict, question: str = "") -> dict:
    """Interprets macro indicators."""
    import asyncio

    q = question or "What does the current macro environment mean for equity markets? What sectors/assets should investors favor?"

    lines = []
    for name, series in macro_data.items():
        if series and series.get("observations"):
            obs = series["observations"]
            latest = obs[-1]
            prev = obs[-2] if len(obs) > 1 else None
            trend = ""
            if prev:
                try:
                    diff = float(latest["value"]) - float(prev["value"])
                    trend = f" (Δ{diff:+.2f})"
                except Exception:
                    pass
            lines.append(f"**{name.upper()}**: {latest['value']}{trend} (as of {latest['date']})")

    context = "\n".join(lines)

    prompt = f"""## Current Macro Data

{context}

---

{q}"""

    loop = asyncio.get_event_loop()

    def _call():
        msg = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text

    text = await loop.run_in_executor(None, _call)
    return {"analysis": text, "question": q}


async def chat_analyst(messages: list, context_data: dict = None) -> str:
    """
    Free-form chat with the analyst.
    messages: [{"role": "user"|"assistant", "content": "..."}]
    """
    import asyncio

    system = SYSTEM_PROMPT
    if context_data:
        system += f"\n\nAvailable context data:\n{json.dumps(context_data, default=str)[:3000]}"

    loop = asyncio.get_event_loop()

    def _call():
        msg = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system,
            messages=messages
        )
        return msg.content[0].text

    return await loop.run_in_executor(None, _call)
