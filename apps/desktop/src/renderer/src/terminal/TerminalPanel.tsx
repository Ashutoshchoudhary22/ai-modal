import { useEffect, useRef } from "react";
import { useTerminalStore } from "../state/terminalStore";
import { useWorkspaceStore } from "../state/workspaceStore";
import { useNotificationStore } from "../state/notificationStore";
import { XtermView } from "./XtermView";
import "./terminal.css";

function isError(v: unknown): boolean {
  return typeof v === "object" && v !== null && "code" in v;
}

export function TerminalPanel() {
  const terminals = useTerminalStore((s) => s.terminals);
  const activeTerminal = useTerminalStore((s) => s.activeTerminal);
  const addTerminal = useTerminalStore((s) => s.addTerminal);
  const workspace = useWorkspaceStore((s) => s.workspace);
  const notify = useNotificationStore((s) => s.notify);
  const bootedRef = useRef(false);

  const newTerminal = async () => {
    const result = await window.desktop.terminal.create(workspace?.rootPath);
    if (isError(result)) {
      notify("error", (result as { message: string }).message);
      return;
    }
    addTerminal(result as Parameters<typeof addTerminal>[0]);
  };

  useEffect(() => {
    if (bootedRef.current || terminals.length > 0) return;
    bootedRef.current = true;
    void newTerminal();
  }, [terminals.length]);

  return (
    <div className="terminal-panel-body">
      {terminals.length === 0 && (
        <div style={{ padding: 8, color: "var(--text-secondary)" }}>Starting terminal...</div>
      )}
      {terminals.map((t) => (
        <div
          key={t.id}
          className="terminal-viewport"
          style={{ display: activeTerminal === t.id ? "flex" : "none" }}
        >
          <XtermView terminalId={t.id} active={activeTerminal === t.id} />
        </div>
      ))}
    </div>
  );
}
