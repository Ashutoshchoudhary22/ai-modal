import { useWorkspaceStore } from "../state/workspaceStore";
import { useSettingsStore } from "../state/settingsStore";
import { useCompletionStore } from "../features/completion/completionStore";

export function StatusBar() {
  const workspace = useWorkspaceStore((s) => s.workspace);
  const { apiStatus, provider, modelId } = useSettingsStore();
  const completionStatus = useCompletionStore((s) => s.status);
  const completionLatency = useCompletionStore((s) => s.lastLatencyMs);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        padding: "2px 12px",
        fontSize: 11,
        borderTop: "1px solid var(--border)",
        background: "var(--bg-tertiary)",
        color: "var(--text-secondary)",
      }}
    >
      <span className={`status-dot ${apiStatus}`} />
      <span>AI: {apiStatus}</span>
      {provider && <span>{provider} / {modelId ?? "default"}</span>}
      <span>|</span>
      <span>Completion: {completionStatus}{completionLatency ? ` (${completionLatency}ms)` : ""}</span>
      {workspace && (
        <>
          <span>|</span>
          <span>{workspace.name}</span>
          <span>Index: {workspace.indexStatus}</span>
          {workspace.gitBranch && <span>Git: {workspace.gitBranch}</span>}
        </>
      )}
    </div>
  );
}
