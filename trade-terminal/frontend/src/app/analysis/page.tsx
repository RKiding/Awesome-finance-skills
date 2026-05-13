"use client";
import { useState, useRef, useEffect } from "react";
import { analysis as analysisApi } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import { BrainCircuit, Globe, Send, RefreshCw, ChevronDown } from "lucide-react";

type Tab = "fundamental" | "macro" | "chat";

export default function AnalysisPage() {
  const [tab, setTab] = useState<Tab>("fundamental");

  // Fundamental
  const [fundSymbol, setFundSymbol] = useState("AAPL");
  const [fundQuestion, setFundQuestion] = useState("");
  const [fundResult, setFundResult] = useState<any>(null);
  const [fundLoading, setFundLoading] = useState(false);

  // Macro
  const [macroQuestion, setMacroQuestion] = useState("");
  const [macroResult, setMacroResult] = useState<any>(null);
  const [macroLoading, setMacroLoading] = useState(false);

  // Chat
  const [chatSymbol, setChatSymbol] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<{ role: string; content: string }[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [chatMessages]);

  const runFundamental = async () => {
    if (!fundSymbol.trim()) return;
    setFundLoading(true);
    const res = await analysisApi.fundamental(fundSymbol.trim(), fundQuestion).catch((e) => ({ error: e.message }));
    setFundResult(res);
    setFundLoading(false);
  };

  const runMacro = async () => {
    setMacroLoading(true);
    const res = await analysisApi.macro(macroQuestion).catch((e) => ({ error: e.message }));
    setMacroResult(res);
    setMacroLoading(false);
  };

  const sendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const userMsg = { role: "user", content: chatInput.trim() };
    const newMessages = [...chatMessages, userMsg];
    setChatMessages(newMessages);
    setChatInput("");
    setChatLoading(true);
    const res = await analysisApi
      .chat(newMessages, chatSymbol || undefined)
      .catch((e) => ({ reply: `Hata: ${e.message}` }));
    setChatMessages([...newMessages, { role: "assistant", content: res.reply }]);
    setChatLoading(false);
  };

  return (
    <div className="flex flex-col h-full min-h-0 gap-4">
      {/* Tabs */}
      <div className="flex gap-1">
        {(["fundamental", "macro", "chat"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`btn ${tab === t ? "btn-blue" : "btn-ghost"}`}
          >
            {t === "fundamental" ? "Temel Analiz" : t === "macro" ? "Makro" : "AI Chat"}
          </button>
        ))}
      </div>

      {/* Fundamental */}
      {tab === "fundamental" && (
        <div className="flex gap-4 flex-1 min-h-0">
          <div className="flex flex-col gap-3 w-72 shrink-0">
            <div className="panel p-3 flex flex-col gap-3">
              <div>
                <label className="text-text-muted text-xs mb-1 block">Sembol</label>
                <input
                  type="text"
                  value={fundSymbol}
                  onChange={(e) => setFundSymbol(e.target.value.toUpperCase())}
                  onKeyDown={(e) => e.key === "Enter" && runFundamental()}
                  placeholder="AAPL"
                  className="w-full px-2 py-1.5 bg-bg-primary border border-bg-border rounded text-xs text-text-primary focus:outline-none focus:border-accent-blue"
                />
              </div>
              <div>
                <label className="text-text-muted text-xs mb-1 block">Soru (opsiyonel)</label>
                <textarea
                  value={fundQuestion}
                  onChange={(e) => setFundQuestion(e.target.value)}
                  placeholder="Bu hisse değerli mi? Büyüme potansiyeli nedir?"
                  rows={3}
                  className="w-full px-2 py-1.5 bg-bg-primary border border-bg-border rounded text-xs text-text-primary focus:outline-none focus:border-accent-blue resize-none"
                />
              </div>
              <button
                className="btn btn-blue flex items-center justify-center gap-2"
                onClick={runFundamental}
                disabled={fundLoading}
              >
                {fundLoading ? <RefreshCw size={12} className="animate-spin" /> : <BrainCircuit size={12} />}
                {fundLoading ? "Analiz ediliyor..." : "Analiz Et"}
              </button>
            </div>

            {/* Raw metrics quick view */}
            {fundResult?.raw_data?.metrics?.metric && (
              <div className="panel p-3 overflow-y-auto">
                <div className="text-text-secondary text-xs font-medium mb-2">Temel Metrikler</div>
                {[
                  ["P/E", "peNormalizedAnnual"],
                  ["P/B", "pbAnnual"],
                  ["ROE %", "roeAnnual"],
                  ["ROA %", "roaAnnual"],
                  ["Net Margin %", "netMarginAnnual"],
                  ["D/E", "debtEquityAnnual"],
                  ["Rev Growth 3Y", "revenueGrowth3Y"],
                ].map(([label, key]) => {
                  const val = fundResult.raw_data.metrics.metric[key];
                  return val != null ? (
                    <div key={key} className="flex justify-between py-0.5 border-b border-bg-border/30">
                      <span className="text-text-muted text-xs">{label}</span>
                      <span className="text-text-primary text-xs">{Number(val).toFixed(2)}</span>
                    </div>
                  ) : null;
                })}
              </div>
            )}
          </div>

          {/* Analysis result */}
          <div className="panel flex-1 overflow-y-auto p-4">
            {!fundResult && !fundLoading && (
              <div className="flex flex-col items-center justify-center h-full text-text-muted gap-2">
                <BrainCircuit size={32} className="opacity-30" />
                <span className="text-sm">Sembol girin ve "Analiz Et"e basın</span>
              </div>
            )}
            {fundLoading && (
              <div className="flex items-center gap-2 text-text-muted">
                <RefreshCw size={14} className="animate-spin" />
                <span className="text-sm">Claude analiz yapıyor...</span>
              </div>
            )}
            {fundResult?.error && (
              <div className="text-accent-red text-sm">{fundResult.error}</div>
            )}
            {fundResult?.analysis && (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown
                  components={{
                    h1: ({ children }) => <h1 className="text-text-primary text-base font-semibold mb-2">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-text-primary text-sm font-semibold mb-1.5 mt-3">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-accent-blue text-xs font-semibold mb-1 mt-2">{children}</h3>,
                    p: ({ children }) => <p className="text-text-secondary text-xs leading-5 mb-2">{children}</p>,
                    li: ({ children }) => <li className="text-text-secondary text-xs leading-5">{children}</li>,
                    ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-0.5">{children}</ul>,
                    strong: ({ children }) => <strong className="text-text-primary font-medium">{children}</strong>,
                    code: ({ children }) => <code className="text-accent-yellow bg-bg-tertiary px-1 rounded text-xs">{children}</code>,
                  }}
                >
                  {fundResult.analysis}
                </ReactMarkdown>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Macro */}
      {tab === "macro" && (
        <div className="flex gap-4 flex-1 min-h-0">
          <div className="w-72 shrink-0 panel p-3 flex flex-col gap-3">
            <div>
              <label className="text-text-muted text-xs mb-1 block">Makro Soru (opsiyonel)</label>
              <textarea
                value={macroQuestion}
                onChange={(e) => setMacroQuestion(e.target.value)}
                placeholder="Mevcut makro ortam hangi sektörler için fırsat sunuyor?"
                rows={4}
                className="w-full px-2 py-1.5 bg-bg-primary border border-bg-border rounded text-xs text-text-primary focus:outline-none focus:border-accent-blue resize-none"
              />
            </div>
            <button
              className="btn btn-blue flex items-center justify-center gap-2"
              onClick={runMacro}
              disabled={macroLoading}
            >
              {macroLoading ? <RefreshCw size={12} className="animate-spin" /> : <Globe size={12} />}
              {macroLoading ? "Analiz ediliyor..." : "Makro Analiz"}
            </button>
            <div className="text-text-muted text-xs mt-1">
              Kaynak: FRED (Federal Reserve) — GDP, CPI, Fed Rate, 10Y Yield, VIX, DXY, WTI Oil
            </div>
          </div>

          <div className="panel flex-1 overflow-y-auto p-4">
            {!macroResult && !macroLoading && (
              <div className="flex flex-col items-center justify-center h-full text-text-muted gap-2">
                <Globe size={32} className="opacity-30" />
                <span className="text-sm">"Makro Analiz"e basın</span>
              </div>
            )}
            {macroLoading && (
              <div className="flex items-center gap-2 text-text-muted">
                <RefreshCw size={14} className="animate-spin" />
                <span className="text-sm">FRED verileri çekiliyor ve analiz yapılıyor...</span>
              </div>
            )}
            {macroResult?.error && <div className="text-accent-red text-sm">{macroResult.error}</div>}
            {macroResult?.analysis && (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown
                  components={{
                    h1: ({ n }) => <h1 className="text-text-primary text-base font-semibold mb-2">{n}</h1>,
                    h2: ({ children }) => <h2 className="text-text-primary text-sm font-semibold mb-1.5 mt-3">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-accent-blue text-xs font-semibold mb-1 mt-2">{children}</h3>,
                    p: ({ children }) => <p className="text-text-secondary text-xs leading-5 mb-2">{children}</p>,
                    li: ({ children }) => <li className="text-text-secondary text-xs leading-5">{children}</li>,
                    ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-0.5">{children}</ul>,
                    strong: ({ children }) => <strong className="text-text-primary font-medium">{children}</strong>,
                  }}
                >
                  {macroResult.analysis}
                </ReactMarkdown>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Chat */}
      {tab === "chat" && (
        <div className="flex flex-col flex-1 panel overflow-hidden min-h-0">
          <div className="flex items-center gap-2 px-3 py-2 border-b border-bg-border">
            <input
              type="text"
              value={chatSymbol}
              onChange={(e) => setChatSymbol(e.target.value.toUpperCase())}
              placeholder="Sembol bağlamı (opsiyonel, AAPL)"
              className="px-2 py-1 bg-bg-primary border border-bg-border rounded text-xs text-text-primary focus:outline-none focus:border-accent-blue w-48"
            />
            <span className="text-text-muted text-xs">Senior equity analyst ile konuş</span>
          </div>

          <div ref={chatRef} className="flex-1 overflow-y-auto p-3 space-y-3">
            {chatMessages.length === 0 && (
              <div className="text-text-muted text-xs text-center py-8">
                Analize başlamak için bir soru yazın. Türkçe veya İngilizce.
              </div>
            )}
            {chatMessages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-2xl rounded px-3 py-2 text-xs leading-5 ${
                    msg.role === "user"
                      ? "bg-accent-blue/20 text-text-primary ml-8"
                      : "bg-bg-tertiary text-text-secondary mr-8"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-1">{children}</p>,
                        li: ({ children }) => <li>{children}</li>,
                        strong: ({ children }) => <strong className="text-text-primary">{children}</strong>,
                        code: ({ children }) => <code className="text-accent-yellow bg-bg-primary px-1 rounded">{children}</code>,
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-bg-tertiary rounded px-3 py-2 text-xs text-text-muted flex items-center gap-2">
                  <RefreshCw size={11} className="animate-spin" /> Düşünüyor...
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 px-3 py-2 border-t border-bg-border">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendChat()}
              placeholder="Sorunuzu yazın... (Enter)"
              className="flex-1 px-2 py-1.5 bg-bg-primary border border-bg-border rounded text-xs text-text-primary focus:outline-none focus:border-accent-blue"
            />
            <button
              className="btn btn-blue flex items-center gap-1"
              onClick={sendChat}
              disabled={chatLoading || !chatInput.trim()}
            >
              <Send size={12} /> Gönder
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
