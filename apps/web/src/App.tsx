import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  chat,
  ChatMessage,
  embed,
  EmbedResponse,
  fetchHealth,
  fetchModels,
  fetchReady,
  GenerateResponse,
  HealthResponse,
  ModelsResponse,
  ReadyResponse,
} from "./api/client";

const DEFAULT_API_URL = "http://localhost:8000";
const STORAGE_KEY = "ai-platform-api-url";

type Tab = "chat" | "embeddings" | "models";

interface UiMessage extends ChatMessage {
  id: string;
}

function uid() {
  return crypto.randomUUID();
}

export default function App() {
  const [apiUrl, setApiUrl] = useState(
    () => localStorage.getItem(STORAGE_KEY) ?? DEFAULT_API_URL,
  );
  const [draftUrl, setDraftUrl] = useState(apiUrl);
  const [tab, setTab] = useState<Tab>("chat");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [ready, setReady] = useState<ReadyResponse | null>(null);
  const [models, setModels] = useState<ModelsResponse | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([
    { id: uid(), role: "system", content: "You are a helpful coding assistant." },
  ]);
  const [input, setInput] = useState("");
  const [stream, setStream] = useState(true);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(512);
  const [loading, setLoading] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);
  const [lastUsage, setLastUsage] = useState<GenerateResponse["usage"] | null>(null);
  const [embedInput, setEmbedInput] = useState("def hello():\n    print('hi')");
  const [embedResult, setEmbedResult] = useState<EmbedResponse | null>(null);
  const [embedError, setEmbedError] = useState<string | null>(null);

  const refreshStatus = useCallback(async () => {
    setStatusError(null);
    try {
      const [healthRes, readyRes] = await Promise.all([
        fetchHealth(apiUrl),
        fetchReady(apiUrl),
      ]);
      setHealth(healthRes);
      setReady(readyRes);
    } catch (error) {
      setHealth(null);
      setReady(null);
      setStatusError(error instanceof Error ? error.message : "Status check failed");
    }
  }, [apiUrl]);

  const loadModels = useCallback(async () => {
    try {
      setModels(await fetchModels(apiUrl));
    } catch (error) {
      setModels(null);
      setStatusError(error instanceof Error ? error.message : "Failed to load models");
    }
  }, [apiUrl]);

  useEffect(() => {
    void refreshStatus();
    const timer = setInterval(() => void refreshStatus(), 15000);
    return () => clearInterval(timer);
  }, [refreshStatus]);

  useEffect(() => {
    if (tab === "models") void loadModels();
  }, [tab, loadModels]);

  const saveApiUrl = () => {
    const next = draftUrl.trim() || DEFAULT_API_URL;
    setApiUrl(next);
    localStorage.setItem(STORAGE_KEY, next);
    void refreshStatus();
  };

  const visibleMessages = useMemo(
    () => messages.filter((m) => m.role !== "system"),
    [messages],
  );

  const sendMessage = async (event: FormEvent) => {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const userMessage: UiMessage = { id: uid(), role: "user", content: text };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setChatError(null);
    setLastUsage(null);

    const payload = nextMessages.map(({ role, content }) => ({ role, content }));

    try {
      if (stream) {
        const assistantId = uid();
        setMessages((prev) => [...prev, { id: assistantId, role: "assistant", content: "" }]);
        const result = await chat(apiUrl, payload, { maxTokens, temperature, stream: true });
        if (typeof result === "object" && "content" in result) {
          throw new Error("Expected stream response");
        }
        let combined = "";
        for await (const chunk of result) {
          combined += chunk;
          const snapshot = combined;
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content: snapshot } : m)),
          );
        }
      } else {
        const result = await chat(apiUrl, payload, { maxTokens, temperature, stream: false });
        if (!(typeof result === "object" && "content" in result)) {
          throw new Error("Expected JSON response");
        }
        setMessages((prev) => [
          ...prev,
          { id: uid(), role: "assistant", content: result.content },
        ]);
        setLastUsage(result.usage);
      }
    } catch (error) {
      setChatError(error instanceof Error ? error.message : "Chat request failed");
    } finally {
      setLoading(false);
    }
  };

  const runEmbeddings = async () => {
    setEmbedError(null);
    setEmbedResult(null);
    const inputs = embedInput.split("\n").map((line) => line.trim()).filter(Boolean);
    if (!inputs.length) {
      setEmbedError("Enter at least one line of text");
      return;
    }
    try {
      setEmbedResult(await embed(apiUrl, inputs));
    } catch (error) {
      setEmbedError(error instanceof Error ? error.message : "Embeddings failed");
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1020] text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-4 p-4 md:p-6">
        <header className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">AI Platform</p>
          <h1 className="text-2xl font-semibold">Test Console</h1>
          <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-end">
            <label className="flex flex-1 flex-col gap-1 text-sm">
              <span className="text-slate-400">API Base URL</span>
              <input
                value={draftUrl}
                onChange={(e) => setDraftUrl(e.target.value)}
                className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2"
              />
            </label>
            <button
              type="button"
              onClick={saveApiUrl}
              className="rounded-xl bg-cyan-500 px-4 py-2 font-medium text-slate-950"
            >
              Connect
            </button>
          </div>
        </header>

        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <aside className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <h2 className="font-medium">Status</h2>
            {statusError ? (
              <p className="mt-3 text-sm text-red-300">{statusError}</p>
            ) : (
              <div className="mt-3 space-y-2 text-sm">
                <p>Health: {health?.status ?? "..."}</p>
                <p>Provider: {ready?.provider ?? "..."}</p>
                <p>Model: {ready?.model_id ?? "none"}</p>
              </div>
            )}
            <div className="mt-4 space-y-2">
              {(["chat", "embeddings", "models"] as Tab[]).map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setTab(key)}
                  className={`block w-full rounded-xl px-3 py-2 text-left capitalize ${
                    tab === key ? "bg-cyan-500/15 text-cyan-300" : "hover:bg-slate-800"
                  }`}
                >
                  {key}
                </button>
              ))}
            </div>
          </aside>

          <main className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            {tab === "chat" && (
              <div className="flex h-[70vh] flex-col">
                <div className="mb-3 flex gap-3 text-sm">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" checked={stream} onChange={(e) => setStream(e.target.checked)} />
                    Stream
                  </label>
                  <label>
                    Temp
                    <input
                      type="number"
                      min={0}
                      max={2}
                      step={0.1}
                      value={temperature}
                      onChange={(e) => setTemperature(Number(e.target.value))}
                      className="ml-2 w-16 rounded border border-slate-700 bg-slate-950 px-2"
                    />
                  </label>
                </div>
                <div className="flex-1 space-y-3 overflow-y-auto">
                  {visibleMessages.map((message) => (
                    <div
                      key={message.id}
                      className={`rounded-xl px-4 py-3 text-sm whitespace-pre-wrap ${
                        message.role === "user"
                          ? "ml-auto max-w-3xl bg-cyan-500/15"
                          : "max-w-3xl bg-slate-950"
                      }`}
                    >
                      {message.content || (loading ? "..." : "")}
                    </div>
                  ))}
                </div>
                {chatError && <p className="mt-2 text-sm text-red-300">{chatError}</p>}
                {lastUsage && (
                  <p className="mt-2 text-xs text-slate-500">
                    Tokens: {lastUsage.total_tokens}
                  </p>
                )}
                <form onSubmit={sendMessage} className="mt-4 flex gap-2">
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    rows={2}
                    className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-3 py-2"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="rounded-xl bg-cyan-500 px-5 py-2 text-slate-950 disabled:opacity-50"
                  >
                    Send
                  </button>
                </form>
              </div>
            )}

            {tab === "embeddings" && (
              <div className="space-y-4">
                <textarea
                  value={embedInput}
                  onChange={(e) => setEmbedInput(e.target.value)}
                  rows={8}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm"
                />
                <button
                  type="button"
                  onClick={() => void runEmbeddings()}
                  className="rounded-xl bg-cyan-500 px-4 py-2 text-slate-950"
                >
                  Generate Embeddings
                </button>
                {embedError && <p className="text-sm text-red-300">{embedError}</p>}
                {embedResult && (
                  <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs">
                    {JSON.stringify(embedResult, null, 2)}
                  </pre>
                )}
              </div>
            )}

            {tab === "models" && (
              <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs">
                {JSON.stringify(models, null, 2)}
              </pre>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
