---
name: klinepic-trade-review
description: Convert completed broker or exchange fills into annotated post-trade candlestick review charts with KLinePic. Use when a user asks to visualize executed trades, review entries and exits, validate a review-chart request, or render a PNG from broker, exchange, CSV, JSON, or MetaTrader fills. Do not use for signals, forecasts, investment advice, or order execution.
---

# KLinePic Trade Review

Turn the user's completed executions into a factual review chart. Keep the workflow post-trade: never recommend the next trade or place an order.

## Workflow

1. Inspect the input.
   - Require executed fills with symbol, time, side, price, and quantity.
   - Use `trade_id` to group entry and exit fills when available.
   - Preserve exchange, position side, fees, and fee asset when supplied.
   - Exclude deposits, withdrawals, transfers, funding-only rows, and unfilled orders.
   - Do not invent missing executions, prices, timestamps, or fees.

2. Select the interface.
   - Prefer the configured KLinePic MCP server and its three tools.
   - If the MCP server is unavailable, use the public repository's documented Docker, GitHub, MCPB, or Agent API path.
   - Never claim a tool ran when it was not available.
   - Keep `KLINEPIC_BASE_URL` unset to use `https://klinepic.com`. Only use a custom base URL when the user explicitly names a trusted HTTPS endpoint; the API key and full trade payload are sent there.

3. Check capabilities.
   - Call `klinepic_get_capabilities` before preparing a chargeable render.
   - Use the returned scopes, limits, remaining quota, and supported endpoints as the source of truth.
   - Never expose the API key in chat, generated files, logs, or commits.

4. Run the free preflight.
   - Call `klinepic_preflight_review_chart` with the proposed fills and chart settings.
   - Treat preflight issues as blockers. Correct the named fields or ask for the missing data, then rerun preflight.
   - Do not substitute a paid render for preflight. A successful preflight validates the request without consuming chart quota.

5. Confirm before rendering.
   - Summarize the symbol, time range, fill count, grouping, and quota impact.
   - Ask for explicit confirmation before calling the render tool when it will consume quota.
   - If the user requested validation only, stop after preflight.

6. Render and report.
   - Call `klinepic_create_review_chart` only after successful preflight and confirmation.
   - Return or save the native PNG result as requested.
   - Label it as a post-trade review and describe only facts visible in the supplied fills and chart.

## Guardrails

- Do not provide trading signals, price predictions, investment advice, position sizing, or order execution.
- Do not turn a historical review into a recommendation about what to buy or sell next.
- Do not send private fills or credentials to an untrusted host.
- Do not hide validation errors or imply that a failed render succeeded.
- Separate user-supplied facts from any interpretation and state uncertainty plainly.

## Public references

- Repository and installation: <https://github.com/sher1096/klinepic-agent-api-examples>
- Agent API guide: <https://klinepic.com/guides/trade-review-chart-api/>
- Sample requests and broker mappings: <https://github.com/sher1096/klinepic-agent-api-examples/tree/master/sample-data>
