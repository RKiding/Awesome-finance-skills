"use client";
import { useState, useEffect } from "react";
import { Save } from "lucide-react";

interface Setting {
  key: string;
  label: string;
  description: string;
  type: "text" | "url";
  env: string;
}

const SETTINGS: Setting[] = [
  { key: "api_url", label: "Backend API URL", description: "FastAPI sunucusunun adresi", type: "url", env: "NEXT_PUBLIC_API_URL" },
  { key: "ws_url", label: "WebSocket URL", description: "WebSocket bağlantı adresi", type: "url", env: "NEXT_PUBLIC_WS_URL" },
];

const API_KEYS: { label: string; key: string; url: string }[] = [
  { label: "Anthropic API Key", key: "ANTHROPIC_API_KEY", url: "https://console.anthropic.com/" },
  { label: "Finnhub API Key", key: "FINNHUB_API_KEY", url: "https://finnhub.io/register" },
  { label: "Twelve Data API Key", key: "TWELVE_DATA_API_KEY", url: "https://twelvedata.com/register" },
  { label: "Alpha Vantage API Key", key: "ALPHA_VANTAGE_API_KEY", url: "https://www.alphavantage.co/support/#api-key" },
  { label: "FRED API Key", key: "FRED_API_KEY", url: "https://fred.stlouisfed.org/docs/api/api_key.html" },
];

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");
  const [wsUrl, setWsUrl] = useState(process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000");
  const [health, setHealth] = useState<"checking" | "ok" | "error">("checking");

  const checkHealth = async () => {
    setHealth("checking");
    try {
      const res = await fetch(`${apiUrl}/api/health`);
      setHealth(res.ok ? "ok" : "error");
    } catch {
      setHealth("error");
    }
  };

  useEffect(() => { checkHealth(); }, [apiUrl]);

  return (
    <div className="max-w-2xl flex flex-col gap-4">
      <h1 className="text-text-primary font-medium text-sm">Ayarlar</h1>

      {/* Backend connection */}
      <div className="panel p-4">
        <h2 className="text-text-secondary text-xs font-medium mb-3">Backend Bağlantısı</h2>

        <div className="flex items-center gap-3 mb-3">
          <span className={`tag ${health === "ok" ? "tag-green" : health === "error" ? "tag-red" : "tag-yellow"}`}>
            {health === "ok" ? "● Bağlı" : health === "error" ? "● Bağlantı yok" : "● Kontrol ediliyor..."}
          </span>
          <button className="btn btn-ghost text-xs" onClick={checkHealth}>Tekrar dene</button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-text-muted text-xs mb-1 block">API URL</label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full px-2 py-1.5 bg-bg-primary border border-bg-border rounded text-xs text-text-primary focus:outline-none focus:border-accent-blue"
            />
          </div>
          <div>
            <label className="text-text-muted text-xs mb-1 block">WebSocket URL</label>
            <input
              type="text"
              value={wsUrl}
              onChange={(e) => setWsUrl(e.target.value)}
              className="w-full px-2 py-1.5 bg-bg-primary border border-bg-border rounded text-xs text-text-primary focus:outline-none focus:border-accent-blue"
            />
          </div>
        </div>
        <p className="text-text-muted text-xs mt-3">
          Bu değerleri değiştirmek için <code className="text-accent-yellow bg-bg-tertiary px-1 rounded">frontend/.env.local</code> dosyasını düzenleyin.
        </p>
      </div>

      {/* API Keys guide */}
      <div className="panel p-4">
        <h2 className="text-text-secondary text-xs font-medium mb-3">API Key Kurulumu</h2>
        <p className="text-text-muted text-xs mb-3">
          API key'leri <code className="text-accent-yellow bg-bg-tertiary px-1 rounded">backend/.env</code> dosyasına ekleyin.
        </p>
        <div className="space-y-2">
          {API_KEYS.map(({ label, key, url }) => (
            <div key={key} className="flex items-center justify-between py-2 border-b border-bg-border/50">
              <div>
                <div className="text-text-primary text-xs">{label}</div>
                <code className="text-text-muted text-xs">{key}</code>
              </div>
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-ghost text-xs"
              >
                Ücretsiz al →
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Cloudflare tunnel */}
      <div className="panel p-4">
        <h2 className="text-text-secondary text-xs font-medium mb-2">Dışarıdan Erişim (Cloudflare Tunnel)</h2>
        <p className="text-text-muted text-xs mb-3">
          Evi dışından erişmek için Cloudflare Tunnel kullanın — ücretsiz, port forwarding gerektirmez.
        </p>
        <div className="bg-bg-primary border border-bg-border rounded p-3 font-mono text-xs text-text-secondary space-y-1">
          <div className="text-text-muted"># Windows PowerShell</div>
          <div>winget install cloudflare.cloudflared</div>
          <div>cloudflared tunnel login</div>
          <div>cloudflared tunnel create trade-terminal</div>
          <div>cloudflared tunnel route dns trade-terminal terminal.senindomain.com</div>
          <div>cloudflared tunnel run trade-terminal</div>
        </div>
        <p className="text-text-muted text-xs mt-2">
          Alternatif: <code className="text-accent-yellow bg-bg-tertiary px-1 rounded">ngrok http 8000</code>
        </p>
      </div>
    </div>
  );
}
