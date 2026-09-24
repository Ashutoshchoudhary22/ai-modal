import { useCallback, useEffect, useRef, useState } from "react";
import { TerminalPanel } from "../terminal/TerminalPanel";
import { TerminalToolbar } from "../terminal/TerminalToolbar";
import { GitPanel } from "../git/GitPanel";
import { AgentEventsPanel } from "../agent/AgentEventsPanel";
import { EvaluationPanel } from "../evaluation/EvaluationPanel";
import "../terminal/terminal.css";

type BottomTab = "terminal" | "problems" | "output" | "git" | "agent" | "evaluation";

interface BottomPanelProps {
  activeTab: BottomTab;
  onTabChange: (tab: BottomTab) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  problems: Array<{ file: string; line: number; message: string; severity: string }>;
}

const TABS: { id: BottomTab; label: string }[] = [
  { id: "terminal", label: "Terminal" },
  { id: "problems", label: "Problems" },
  { id: "output", label: "Output" },
  { id: "git", label: "Git" },
  { id: "agent", label: "Agent" },
  { id: "evaluation", label: "Evaluation" },
];

const DEFAULT_HEIGHT = 280;
const MIN_HEIGHT = 120;
const MAX_HEIGHT_RATIO = 0.6;

export function BottomPanel({
  activeTab,
  onTabChange,
  collapsed,
  onToggleCollapse,
  problems,
}: BottomPanelProps) {
  const [panelHeight, setPanelHeight] = useState(DEFAULT_HEIGHT);
  const resizingRef = useRef(false);
  const startYRef = useRef(0);
  const startHeightRef = useRef(DEFAULT_HEIGHT);

  const onResizeStart = useCallback(
    (e: React.MouseEvent) => {
      if (collapsed) return;
      resizingRef.current = true;
      startYRef.current = e.clientY;
      startHeightRef.current = panelHeight;
      e.preventDefault();
    },
    [collapsed, panelHeight],
  );

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!resizingRef.current) return;
      const maxHeight = Math.floor(window.innerHeight * MAX_HEIGHT_RATIO);
      const delta = startYRef.current - e.clientY;
      const next = Math.min(maxHeight, Math.max(MIN_HEIGHT, startHeightRef.current + delta));
      setPanelHeight(next);
    };
    const onUp = () => {
      resizingRef.current = false;
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  return (
    <div
      className="bottom-panel"
      style={collapsed ? undefined : { height: panelHeight + 28 }}
    >
      {!collapsed && <div className="bottom-panel-resize-handle" onMouseDown={onResizeStart} />}
      <div className="bottom-panel-header">
        <div className="bottom-panel-tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`bottom-panel-tab${activeTab === tab.id ? " active" : ""}`}
              onClick={() => {
                onTabChange(tab.id);
                if (collapsed) onToggleCollapse();
              }}
            >
              {tab.label}
              {tab.id === "problems" && problems.length > 0 && ` (${problems.length})`}
            </button>
          ))}
        </div>
        {activeTab === "terminal" && !collapsed ? (
          <TerminalToolbar onCollapse={onToggleCollapse} />
        ) : (
          <button
            type="button"
            className="bottom-panel-collapse"
            style={{ marginLeft: "auto" }}
            title={collapsed ? "Show Panel" : "Hide Panel"}
            onClick={onToggleCollapse}
          >
            {collapsed ? "▲" : "▼"}
          </button>
        )}
      </div>
      {!collapsed && (
        <div className="bottom-panel-content" style={{ height: panelHeight }}>
          {activeTab === "terminal" && <TerminalPanel />}
          {activeTab === "problems" && (
            <div style={{ padding: 8, overflow: "auto", height: "100%" }}>
              {problems.length === 0 && <div style={{ color: "var(--text-secondary)" }}>No problems</div>}
              {problems.map((p, i) => (
                <div key={i} style={{ padding: "2px 0", fontSize: 12 }}>
                  <span style={{ color: p.severity === "error" ? "var(--error)" : "var(--warning)" }}>
                    [{p.severity}]
                  </span>{" "}
                  {p.file}:{p.line} — {p.message}
                </div>
              ))}
            </div>
          )}
          {activeTab === "output" && (
            <div style={{ padding: 8, color: "var(--text-secondary)" }}>Output panel</div>
          )}
          {activeTab === "git" && <GitPanel />}
          {activeTab === "agent" && <AgentEventsPanel />}
          {activeTab === "evaluation" && <EvaluationPanel />}
        </div>
      )}
    </div>
  );
}
