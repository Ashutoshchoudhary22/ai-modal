import { useEffect, useRef, useState } from "react";
import { useTerminalStore } from "../state/terminalStore";
import { useWorkspaceStore } from "../state/workspaceStore";
import { useNotificationStore } from "../state/notificationStore";

function isError(v: unknown): boolean {
  return typeof v === "object" && v !== null && "code" in v;
}

export function TerminalPanel() {
  const terminals = useTerminalStore((s) => s.terminals);
  const activeTerminal = useTerminalStore((s) => s.activeTerminal);
  const addTerminal = useTerminalStore((s) => s.addTerminal);
  const appendLine = useTerminalStore((s) => s.appendLine);
  const workspace = useWorkspaceStore((s) => s.workspace);
  const notify = useNotificationStore((s) => s.notify);
  const [input, setInput] = useState("");
  const outputRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const unsub = window.desktop.terminal.onOutput((event) => {
      appendLine(event.terminalId, {
        type: event.type === "stderr" ? "stderr" : event.type === "error" ? "error" : "stdout",
        text: event.data,
      });
    });
    return unsub;
  }, [appendLine]);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [terminals, activeTerminal]);

  const newTerminal = async () => {
    const result = await window.desktop.terminal.create(workspace?.rootPath);
    if (isError(result)) {
      notify("error", (result as { message: string }).message);
      return;
    }
    addTerminal(result as Parameters<typeof addTerminal>[0]);
  };

  const runCommand = async () => {
    if (!activeTerminal || !input.trim()) return;
    appendLine(activeTerminal, { type: "input", text: `$ ${input}` });
    const result = await window.desktop.terminal.execute(activeTerminal, input);
    if (isError(result)) {
      notify("error", (result as { message: string }).message);
    }
    setInput("");
  };

  const active = terminals.find((t) => t.id === activeTerminal);

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", fontFamily: "var(--font-mono)" }}>
      <div style={{ display: "flex", gap: 4, padding: 4, borderBottom: "1px solid var(--border)" }}>
        <button onClick={() => void newTerminal()}>+ New Terminal</button>
        {terminals.map((t) => (
          <button
            key={t.id}
            onClick={() => useTerminalStore.getState().setActiveTerminal(t.id)}
            style={{ opacity: activeTerminal === t.id ? 1 : 0.6 }}
          >
            Terminal {t.id.slice(0, 6)}
          </button>
        ))}
      </div>
      <div ref={outputRef} style={{ flex: 1, overflow: "auto", padding: 8, fontSize: 12 }}>
        {!active && (
          <div style={{ color: "var(--text-secondary)" }}>No terminal — click New Terminal</div>
        )}
        {active?.lines.map((line, i) => (
          <div
            key={i}
            style={{
              color:
                line.type === "stderr" || line.type === "error"
                  ? "var(--error)"
                  : line.type === "input"
                    ? "var(--accent)"
                    : "var(--text-primary)",
              whiteSpace: "pre-wrap",
            }}
          >
            {line.text}
          </div>
        ))}
      </div>
      <div style={{ display: "flex", padding: 4, borderTop: "1px solid var(--border)" }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void runCommand();
          }}
          placeholder="Enter command..."
          style={{ flex: 1, fontFamily: "var(--font-mono)" }}
          disabled={!activeTerminal}
        />
      </div>
    </div>
  );
}
