"use client";
import { useEffect, useState, useRef } from "react";
import { bots as botApi } from "@/lib/api";
import { Play, Square, Plus, Trash2, RefreshCw, Terminal, Settings2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function BotsPage() {
  const [botList, setBotList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [showRegister, setShowRegister] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [editConfig, setEditConfig] = useState("{}");
  const [registerForm, setRegisterForm] = useState({ id: "", name: "", script_path: "", description: "" });
  const logRef = useRef<HTMLDivElement>(null);

  const refresh = async () => {
    const list = await botApi.list().catch(() => []);
    setBotList(list);
    setLoading(false);
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5_000);
    return () => clearInterval(id);
  }, []);

  const selectBot = async (bot: any) => {
    setSelected(bot);
    setShowConfig(false);
    const { logs: l } = await botApi.logs(bot.id, 200).catch(() => ({ logs: [] }));
    setLogs(l);
  };

  useEffect(() => {
    if (!selected) return;
    const id = setInterval(async () => {
      const { logs: l } = await botApi.logs(selected.id, 200).catch(() => ({ logs: [] }));
      setLogs(l);
    }, 3_000);
    return () => clearInterval(id);
  }, [selected]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const startBot = async (id: string) => {
    await botApi.start(id).catch(alert);
    refresh();
  };

  const stopBot = async (id: string) => {
    await botApi.stop(id).catch(alert);
    refresh();
  };

  const deleteBot = async (id: string) => {
    if (!confirm(`"${id}" silinsin mi?`)) return;
    await botApi.delete(id).catch(alert);
    if (selected?.id === id) setSelected(null);
    refresh();
  };

  const registerBot = async () => {
    await botApi.register(registerForm).catch(alert);
    setShowRegister(false);
    setRegisterForm({ id: "", name: "", script_path: "", description: "" });
    refresh();
  };

  const saveConfig = async () => {
    try {
      const cfg = JSON.parse(editConfig);
      await botApi.updateConfig(selected.id, cfg);
      setShowConfig(false);
      refresh();
    } catch {
      alert("Geçersiz JSON");
    }
  };

  return (
    <div className="flex gap-4 h-full min-h-0">
      {/* Bot list */}
      <div className="w-64 shrink-0 panel flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-3 py-2 border-b border-bg-border">
          <span className="text-text-secondary text-xs font-medium">Botlar ({botList.length})</span>
          <button className="btn btn-blue flex items-center gap-1" onClick={() => setShowRegister(true)}>
            <Plus size={12} /> Ekle
          </button>
        </div>

        <div className="overflow-y-auto flex-1">
          {loading && <div className="text-text-muted text-xs p-3">Yükleniyor...</div>}
          {!loading && botList.length === 0 && (
            <div className="text-text-muted text-xs p-3">Henüz bot yok. "Ekle" ile kaydet.</div>
          )}
          {botList.map((bot) => (
            <button
              key={bot.id}
              onClick={() => selectBot(bot)}
              className={`w-full px-3 py-3 text-left hover:bg-bg-tertiary border-b border-bg-border/50 transition-colors ${
                selected?.id === bot.id ? "bg-bg-tertiary" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-text-primary text-xs font-medium truncate">{bot.name}</span>
                <span className={`tag ${bot.status === "running" ? "tag-green" : "tag-blue"}`}>
                  {bot.status === "running" ? "●" : "○"}
                </span>
              </div>
              <div className="text-text-muted text-xs mt-0.5 truncate">{bot.id}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Detail panel */}
      <div className="flex-1 flex flex-col gap-3 min-w-0">
        {!selected ? (
          <div className="panel flex-1 flex items-center justify-center">
            <span className="text-text-muted text-sm">Bir bot seçin</span>
          </div>
        ) : (
          <>
            {/* Bot header */}
            <div className="panel p-3 flex items-center gap-3 flex-wrap">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-text-primary font-medium">{selected.name}</span>
                  <span className={`tag ${selected.status === "running" ? "tag-green" : "tag-blue"}`}>
                    {selected.status}
                  </span>
                </div>
                <div className="text-text-muted text-xs mt-0.5">{selected.script_path}</div>
                {selected.description && (
                  <div className="text-text-secondary text-xs mt-1">{selected.description}</div>
                )}
              </div>
              <div className="flex items-center gap-2">
                {selected.status !== "running" ? (
                  <button className="btn btn-green flex items-center gap-1" onClick={() => startBot(selected.id)}>
                    <Play size={12} /> Başlat
                  </button>
                ) : (
                  <button className="btn btn-red flex items-center gap-1" onClick={() => stopBot(selected.id)}>
                    <Square size={12} /> Durdur
                  </button>
                )}
                <button
                  className="btn btn-ghost flex items-center gap-1"
                  onClick={() => {
                    setEditConfig(JSON.stringify(selected.config || {}, null, 2));
                    setShowConfig(!showConfig);
                  }}
                >
                  <Settings2 size={12} /> Ayarlar
                </button>
                <button className="btn btn-ghost flex items-center gap-1 text-accent-red/70 hover:text-accent-red" onClick={() => deleteBot(selected.id)}>
                  <Trash2 size={12} />
                </button>
              </div>
            </div>

            {/* Config editor */}
            {showConfig && (
              <div className="panel p-3">
                <div className="text-text-secondary text-xs mb-2 font-medium">Bot Parametreleri (JSON)</div>
                <textarea
                  value={editConfig}
                  onChange={(e) => setEditConfig(e.target.value)}
                  className="w-full h-32 bg-bg-primary border border-bg-border rounded p-2 text-xs font-mono text-text-primary focus:outline-none focus:border-accent-blue resize-y"
                />
                <div className="flex gap-2 mt-2">
                  <button className="btn btn-blue" onClick={saveConfig}>Kaydet</button>
                  <button className="btn btn-ghost" onClick={() => setShowConfig(false)}>İptal</button>
                </div>
                <div className="text-text-muted text-xs mt-2">
                  Not: Parametreler bot'a <code>BOT_*</code> env vars olarak aktarılır.
                </div>
              </div>
            )}

            {/* Logs */}
            <div className="panel flex-1 flex flex-col overflow-hidden" style={{ minHeight: 200 }}>
              <div className="flex items-center justify-between px-3 py-2 border-b border-bg-border">
                <span className="text-text-secondary text-xs font-medium flex items-center gap-1.5">
                  <Terminal size={12} /> Log ({logs.length} satır)
                </span>
                <button
                  onClick={async () => {
                    const { logs: l } = await botApi.logs(selected.id, 500).catch(() => ({ logs: [] }));
                    setLogs(l);
                  }}
                  className="text-text-muted hover:text-text-secondary"
                >
                  <RefreshCw size={12} />
                </button>
              </div>
              <div
                ref={logRef}
                className="flex-1 overflow-y-auto p-3 font-mono text-xs text-text-secondary leading-5"
              >
                {logs.length === 0 ? (
                  <span className="text-text-muted">Henüz log yok.</span>
                ) : (
                  logs.map((line, i) => (
                    <div key={i} className={
                      line.includes("ERROR") ? "text-accent-red" :
                      line.includes("WARN") ? "text-accent-yellow" :
                      line.includes("started") || line.includes("INFO") ? "text-accent-green" : ""
                    }>
                      {line || " "}
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Register modal */}
      {showRegister && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="panel p-5 w-96">
            <h2 className="text-text-primary font-medium mb-4">Bot Kaydet</h2>
            {[
              { key: "id", label: "ID (benzersiz)", placeholder: "macd_bot" },
              { key: "name", label: "İsim", placeholder: "MACD Stratejisi" },
              { key: "script_path", label: "Script Yolu", placeholder: "C:/bots/macd_bot.py" },
              { key: "description", label: "Açıklama (opsiyonel)", placeholder: "" },
            ].map(({ key, label, placeholder }) => (
              <div key={key} className="mb-3">
                <label className="text-text-secondary text-xs mb-1 block">{label}</label>
                <input
                  type="text"
                  value={(registerForm as any)[key]}
                  onChange={(e) => setRegisterForm((f) => ({ ...f, [key]: e.target.value }))}
                  placeholder={placeholder}
                  className="w-full px-2 py-1.5 bg-bg-primary border border-bg-border rounded text-xs text-text-primary focus:outline-none focus:border-accent-blue"
                />
              </div>
            ))}
            <div className="flex gap-2 mt-4">
              <button className="btn btn-blue flex-1" onClick={registerBot}>Kaydet</button>
              <button className="btn btn-ghost flex-1" onClick={() => setShowRegister(false)}>İptal</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
