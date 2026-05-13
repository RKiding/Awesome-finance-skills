"use client";
import { useEffect, useRef, useState } from "react";
import { Search, Wifi, WifiOff } from "lucide-react";
import { market } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function Topbar() {
  const [connected, setConnected] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const router = useRouter();
  const timer = useRef<any>(null);

  useEffect(() => {
    const check = async () => {
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/health`);
        setConnected(true);
      } catch {
        setConnected(false);
      }
    };
    check();
    const id = setInterval(check, 10_000);
    return () => clearInterval(id);
  }, []);

  const handleSearch = (v: string) => {
    setQuery(v);
    clearTimeout(timer.current);
    if (!v.trim()) { setResults([]); return; }
    timer.current = setTimeout(async () => {
      const res = await market.search(v).catch(() => []);
      setResults(res.slice(0, 6));
    }, 350);
  };

  return (
    <header className="h-11 flex items-center px-4 bg-bg-secondary border-b border-bg-border gap-4 shrink-0">
      {/* Search */}
      <div className="relative flex-1 max-w-xs">
        <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          placeholder="Sembol ara... (AAPL, BTCUSDT)"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          className="w-full pl-7 pr-3 py-1.5 bg-bg-tertiary border border-bg-border rounded text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-blue"
        />
        {results.length > 0 && (
          <div className="absolute top-full mt-1 left-0 right-0 panel z-50 py-1">
            {results.map((r, i) => (
              <button
                key={i}
                className="w-full px-3 py-1.5 text-left hover:bg-bg-tertiary flex justify-between items-center"
                onClick={() => {
                  setQuery("");
                  setResults([]);
                  router.push(`/?symbol=${r.symbol}`);
                }}
              >
                <span className="text-accent-blue font-medium">{r.symbol}</span>
                <span className="text-text-muted truncate ml-2 text-xs">{r.name}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="ml-auto flex items-center gap-2 text-xs">
        <span className={connected ? "text-accent-green" : "text-accent-red"}>
          {connected ? <Wifi size={13} /> : <WifiOff size={13} />}
        </span>
        <span className={connected ? "text-accent-green" : "text-accent-red"}>
          {connected ? "Bağlı" : "Bağlantı yok"}
        </span>
        <span className="text-text-muted">|</span>
        <span className="text-text-muted">{new Date().toLocaleDateString("tr-TR")}</span>
      </div>
    </header>
  );
}
