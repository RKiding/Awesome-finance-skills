"use client";
import { useEffect, useState } from "react";
import { createLiveFeed } from "@/lib/api";
import { TrendingUp, TrendingDown } from "lucide-react";

interface Props {
  symbol: string;
}

export default function QuoteTicker({ symbol }: Props) {
  const [quote, setQuote] = useState<any>(null);
  const [flash, setFlash] = useState<"up" | "down" | null>(null);
  const [prevPrice, setPrevPrice] = useState<number | null>(null);

  useEffect(() => {
    if (!symbol) return;
    const feed = createLiveFeed();

    feed.ws.addEventListener("open", () => feed.subscribe(symbol));
    feed.onQuote((data) => {
      if (data.symbol?.toUpperCase() !== symbol.toUpperCase()) return;
      setQuote(data);
      if (prevPrice !== null && data.price !== null) {
        setFlash(data.price > prevPrice ? "up" : "down");
        setTimeout(() => setFlash(null), 600);
      }
      setPrevPrice(data.price);
    });

    return () => feed.close();
  }, [symbol]);

  if (!quote) return (
    <div className="flex items-center gap-2 text-text-muted animate-pulse">
      <span className="text-sm">{symbol}</span>
      <span className="text-xs">Yükleniyor...</span>
    </div>
  );

  const chgPct = quote.change_pct ?? 0;
  const isPos = chgPct >= 0;

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <span className="text-text-secondary text-sm font-medium">{symbol}</span>
      <span
        className={`text-xl font-semibold transition-colors duration-300 ${
          flash === "up" ? "text-accent-green" : flash === "down" ? "text-accent-red" : "text-text-primary"
        }`}
      >
        {quote.price != null ? Number(quote.price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 }) : "—"}
      </span>
      <span className={`flex items-center gap-1 text-sm ${isPos ? "positive" : "negative"}`}>
        {isPos ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
        {isPos ? "+" : ""}{chgPct.toFixed(2)}%
      </span>
      {quote.high && (
        <span className="text-xs text-text-muted">
          H: {Number(quote.high).toLocaleString(undefined, { maximumFractionDigits: 4 })}
          {" "}L: {Number(quote.low).toLocaleString(undefined, { maximumFractionDigits: 4 })}
        </span>
      )}
      {quote.source && (
        <span className="tag tag-blue ml-auto">{quote.source}</span>
      )}
    </div>
  );
}
