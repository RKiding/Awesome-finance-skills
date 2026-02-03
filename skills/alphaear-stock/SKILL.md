---
name: alphaear-stock
description: Search A-Share finance stock tickers and retrieve finance stock price history. Use when user asks about finance stock codes, recent price changes, or specific company finance stock info.
---

# AlphaEar Stock Skill

## Overview

Search A-Share/HK stock tickers and retrieve historical price data (OHLCV).

## Capabilities

### 1. Stock Search & Data

Use `scripts/stock_tools.py` via `StockTools`.

-   **Search**: `search_ticker(query)`
    -   Fuzzy search by code or name (e.g., "Moutai", "600519").
    -   Returns: List of `{code, name}`.
-   **Get Price**: `get_stock_price(ticker, start_date, end_date)`
    -   Returns DataFrame with OHLCV data.
    -   Dates format: "YYYY-MM-DD".

## Dependencies

-   `pandas`, `requests`
-   `scripts/database_manager.py` (stock tables)
