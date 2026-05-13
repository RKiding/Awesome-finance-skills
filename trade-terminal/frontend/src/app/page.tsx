"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import TradingViewWidget from "@/components/charts/TradingViewWidget";
import QuoteTicker from "@/components/charts/QuoteTicker";
import { market } from "@/lib/api";
import { RefreshCw } from "lucide-react";

const INTERVALS: { label: string; tv: string; api: string }[] = [
  { label: "1m", tv: "1", api: "1min" },
  { label: "5m", tv: "5", api: "5min" },
  { label: "15m", tv: "15", api: "15min" },
  { label: "1h", tv: "60", api: "1h" },
  { label: "4h", tv: "240", api: "4h" },
  { label: "1D", tv: "D", api: "1day" },
  { label: "1W", tv: "W", api: "1week" },
];

const WATCHLIST_DEFAULT = ["AAPL", "MSFT", "BTCUSDT", "ETHUSDT", "NVDA", "TSLA"];

export default function DashboardPage() {
  const params = useSearchParams();
  const [symbol, setSymbol] = useState(params.get("symbol") || "AAPL");
  const [interval, setInterval] = useState(INTERVALS[5]);
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [loadingWL, setLoadingWL] = useState(true);

  useEffect(() => {
    const sym = params.get("symbol");
    if (sym) setSymbol(sym.toUpperCase());
  }, [params]);

  const refreshWatchlist = async () => {
    setLoadingWL(true);
    const res = await market.quotes(WATCHLIST_DEFAULT).catch(() => ({}));
    setWatchlist(Object.values(res));
    setLoadingWL(false);
  };

  useEffect(() => {
    refreshWatchlist();
    const id = setInterval(refreshWatchlist, 15_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex gap-4 h-full min-h-0">
      {/* Main chart area */}
      <div className="flex-1 flex flex-col gap-3 min-w-0">
        <div className="panel p-3">
          <QuoteTicker symbol={symbol} />
        </div>

        <div className="panel p-0 overflow-hidden flex-1" style={{ minHeight: 480 }}>
          {/* Interval selector */}
          <div className="flex items-center gap-1 px-3 py-2 border-b border-bg-border">
            {INTERVALS.map((iv) => (
              <button
                key={iv.tv}
                onClick={() => setInterval(iv)}
                className={`btn ${interval.tv === iv.tv ? "btn-blue" : "btn-ghost"}`}
              >
                {iv.label}
              </button>
            ))}
            <div className="ml-auto text-xs text-text-muted">TradingView</div>
          </div>
          <TradingViewWidget symbol={symbol} interval={interval.tv} height={460} />
        </div>
      </div>

      {/* Watchlist */}
      <div className="w-56 shrink-0 flex flex-col panel overflow-hidden">
        <div className="flex items-center justify-between px-3 py-2 border-b border-bg-border">
          <span className="text-text-secondary text-xs font-medium">Watchlist</span>
          <button onClick={refreshWatchlist} className="text-text-muted hover:text-text-secondary">
            <RefreshCw size={12} className={loadingWL ? "animate-spin" : ""} />
          </button>
        </div>
        <div className="overflow-y-auto flex-1">
          {watchlist.map((q) => {
            if (!q?.symbol) return null;
            const chg = q.change_pct ?? 0;
            const isPos = chg >= 0;
            return (
              <button
                key={q.symbol}
                className={`w-full px-3 py-2.5 text-left hover:bg-bg-tertiary border-b border-bg-border/50 transition-colors ${
                  symbol === q.symbol ? "bg-bg-tertiary" : ""
                }`}
                onClick={() => setSymbol(q.symbol)}
              >
                <div className="flex justify-between items-center">
                  <span className="text-accent-blue text-xs font-medium">{q.symbol}</span>
                  <span className={`text-xs ${isPos ? "positive" : "negative"}`}>
                    {isPos ? "+" : ""}{chg.toFixed(2)}%
                  </span>
                </div>
                <div className="text-text-primary text-xs mt-0.5">
                  {q.price != null
                    ? Number(q.price).toLocaleString(undefined, { maximumFractionDigits: 4 })
                    : "—"}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
