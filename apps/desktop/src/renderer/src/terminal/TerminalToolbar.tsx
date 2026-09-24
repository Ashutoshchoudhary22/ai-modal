import { useTerminalStore } from "../state/terminalStore";
import { useWorkspaceStore } from "../state/workspaceStore";
import { useNotificationStore } from "../state/notificationStore";
import "./terminal.css";

function isError(v: unknown): boolean {
  return typeof v === "object" && v !== null && "code" in v;
}

interface TerminalToolbarProps {
  onCollapse: () => void;
}

export function TerminalToolbar({ onCollapse }: TerminalToolbarProps) {
  const terminals = useTerminalStore((s) => s.terminals);
  const activeTerminal = useTerminalStore((s) => s.activeTerminal);
  const addTerminal = useTerminalStore((s) => s.addTerminal);
  const removeTerminal = useTerminalStore((s) => s.removeTerminal);
  const workspace = useWorkspaceStore((s) => s.workspace);
  const notify = useNotificationStore((s) => s.notify);

  const newTerminal = async () => {
    const result = await window.desktop.terminal.create(workspace?.rootPath);
    if (isError(result)) {
      notify("error", (result as { message: string }).message);
      return;
    }
    addTerminal(result as Parameters<typeof addTerminal>[0]);
  };

  const closeTerminal = async (id: string) => {
    const isLast = terminals.length === 1;
    await window.desktop.terminal.kill(id);
    removeTerminal(id);
    if (isLast) {
      void newTerminal();
    }
  };

  const killActive = async () => {
    if (!activeTerminal) return;
    await closeTerminal(activeTerminal);
  };

  const clearActive = async () => {
    if (!activeTerminal) return;
    await window.desktop.terminal.clear(activeTerminal);
  };

  return (
    <div className="terminal-toolbar">
      <div className="terminal-tabs">
        {terminals.map((t) => (
          <div
            key={t.id}
            className={`terminal-tab${activeTerminal === t.id ? " active" : ""}`}
          >
            <button
              type="button"
              className="terminal-tab-label"
              onClick={() => useTerminalStore.getState().setActiveTerminal(t.id)}
            >
              {t.session.title}
            </button>
            <button
              type="button"
              className="terminal-tab-close"
              title="Kill Terminal"
              onClick={() => void closeTerminal(t.id)}
            >
              ×
            </button>
          </div>
        ))}
      </div>
      <div className="terminal-actions">
        <button type="button" className="terminal-icon-btn" title="New Terminal" onClick={() => void newTerminal()}>
          +
        </button>
        <button type="button" className="terminal-icon-btn" title="Split Terminal" onClick={() => void newTerminal()}>
          ⧉
        </button>
        <button type="button" className="terminal-icon-btn" title="Kill Terminal" onClick={() => void killActive()}>
          ✕
        </button>
        <button type="button" className="terminal-icon-btn" title="Clear Terminal" onClick={() => void clearActive()}>
          ⋯
        </button>
        <button type="button" className="terminal-icon-btn bottom-panel-collapse" title="Hide Panel" onClick={onCollapse}>
          ▼
        </button>
      </div>
    </div>
  );
}
