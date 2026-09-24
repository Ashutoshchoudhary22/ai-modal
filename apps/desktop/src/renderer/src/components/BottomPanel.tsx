import { TerminalPanel } from "../terminal/TerminalPanel";
import { GitPanel } from "../git/GitPanel";
import { AgentEventsPanel } from "../agent/AgentEventsPanel";
import { EvaluationPanel } from "../evaluation/EvaluationPanel";

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

export function BottomPanel({
  activeTab,
  onTabChange,
  collapsed,
  onToggleCollapse,
  problems,
}: BottomPanelProps) {
  return (
    <div style={{ borderTop: "1px solid var(--border)", display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", background: "var(--bg-tertiary)" }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              onTabChange(tab.id);
              if (collapsed) onToggleCollapse();
            }}
            style={{
              padding: "4px 12px",
              border: "none",
              borderBottom: activeTab === tab.id ? "2px solid var(--accent)" : "2px solid transparent",
              background: "transparent",
            }}
          >
            {tab.label}
            {tab.id === "problems" && problems.length > 0 && ` (${problems.length})`}
          </button>
        ))}
        <button onClick={onToggleCollapse} style={{ marginLeft: "auto", border: "none" }}>
          {collapsed ? "▲" : "▼"}
        </button>
      </div>
      {!collapsed && (
        <div style={{ height: 200, overflow: "hidden" }}>
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
