"use client";
import { useEffect, useRef } from "react";

interface Props {
  symbol: string;
  interval?: string;
  height?: number;
}

// Embeds the official TradingView Advanced Chart Widget (free, personal use)
export default function TradingViewWidget({ symbol, interval = "D", height = 500 }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const scriptRef = useRef<HTMLScriptElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    ref.current.innerHTML = "";

    const container = document.createElement("div");
    container.className = "tradingview-widget-container__widget";
    ref.current.appendChild(container);

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: symbol,
      interval: interval,
      timezone: "Europe/Istanbul",
      theme: "dark",
      style: "1",
      locale: "tr",
      backgroundColor: "#161b22",
      gridColor: "rgba(48,54,61,0.3)",
      hide_top_toolbar: false,
      hide_legend: false,
      save_image: false,
      calendar: false,
      hide_volume: false,
      support_host: "https://www.tradingview.com",
    });

    ref.current.appendChild(script);
    scriptRef.current = script;

    return () => {
      if (ref.current) ref.current.innerHTML = "";
    };
  }, [symbol, interval]);

  return (
    <div
      ref={ref}
      className="tradingview-widget-container w-full"
      style={{ height }}
    />
  );
}
