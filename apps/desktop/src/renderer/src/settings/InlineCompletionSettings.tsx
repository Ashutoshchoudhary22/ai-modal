import { useSettingsStore } from "../state/settingsStore";
import { useCompletionStore } from "../features/completion/completionStore";
import { cancelActiveCompletion } from "../features/completion/completionBridge";

export function InlineCompletionSettings() {
  const { settings, apiStatus, provider, modelId, updateSettings } = useSettingsStore();
  const completionStatus = useCompletionStore((s) => s.status);
  const telemetry = useCompletionStore((s) => s.telemetry);

  if (!settings) {
    return <div style={{ padding: 12, color: "var(--text-secondary)" }}>Loading settings…</div>;
  }

  const mod = window.desktop.platform.isMac ? "Cmd" : "Ctrl";

  const onToggle = async (key: keyof typeof settings, value: boolean | number | string) => {
    await updateSettings({ [key]: value });
    if (key === "inlineCompletionEnabled") {
      const enabled = Boolean(value);
      useCompletionStore.getState().setEnabled(enabled);
      if (!enabled) cancelActiveCompletion();
    }
  };

  return (
    <div style={{ padding: 12, overflow: "auto", height: "100%" }}>
      <h3 style={{ margin: "0 0 12px", fontSize: 14 }}>AI → Inline Completion</h3>
      <p style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 16 }}>
        Copilot-style ghost text in the editor. Service: {apiStatus}
        {apiStatus !== "connected" && " — completions unavailable while disconnected"}
      </p>

      <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <input
          type="checkbox"
          aria-label="Enable inline completion"
          checked={settings.inlineCompletionEnabled}
          onChange={(e) => void onToggle("inlineCompletionEnabled", e.target.checked)}
        />
        Enable inline completion
      </label>

      <label style={{ display: "block", marginBottom: 12, fontSize: 12 }}>
        Model
        <input
          type="text"
          value={settings.completionModel}
          onChange={(e) => void onToggle("completionModel", e.target.value)}
          style={{ display: "block", width: "100%", marginTop: 4 }}
        />
      </label>

      <div style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 12 }}>
        Provider: {provider ?? "—"} | Active model: {modelId ?? settings.defaultModel}
      </div>

      <label style={{ display: "block", marginBottom: 12, fontSize: 12 }}>
        Debounce (ms)
        <input
          type="number"
          aria-label="Debounce (ms)"
          min={100}
          max={1000}
          value={settings.completionDebounceMs}
          onChange={(e) => void onToggle("completionDebounceMs", Number(e.target.value))}
          style={{ display: "block", width: "100%", marginTop: 4 }}
        />
      </label>

      <label style={{ display: "block", marginBottom: 12, fontSize: 12 }}>
        Max completion tokens
        <input
          type="number"
          min={32}
          max={2048}
          value={settings.completionMaxTokens}
          onChange={(e) => void onToggle("completionMaxTokens", Number(e.target.value))}
          style={{ display: "block", width: "100%", marginTop: 4 }}
        />
      </label>

      <label style={{ display: "block", marginBottom: 12, fontSize: 12 }}>
        Context lines (nearby code)
        <input
          type="number"
          min={10}
          max={200}
          value={settings.completionContextLines}
          onChange={(e) => void onToggle("completionContextLines", Number(e.target.value))}
          style={{ display: "block", width: "100%", marginTop: 4 }}
        />
      </label>

      <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <input
          type="checkbox"
          aria-label="Include bounded repository context (indexer)"
          checked={settings.completionRepositoryContextEnabled}
          onChange={(e) => void onToggle("completionRepositoryContextEnabled", e.target.checked)}
        />
        Include bounded repository context (indexer)
      </label>

      <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <input
          type="checkbox"
          checked={settings.completionTriggerOnTyping}
          onChange={(e) => void onToggle("completionTriggerOnTyping", e.target.checked)}
        />
        Trigger on typing
      </label>

      <label style={{ display: "block", marginBottom: 12, fontSize: 12 }}>
        Max requests per minute
        <input
          type="number"
          min={10}
          max={120}
          value={settings.completionMaxRequestsPerMinute}
          onChange={(e) => void onToggle("completionMaxRequestsPerMinute", Number(e.target.value))}
          style={{ display: "block", width: "100%", marginTop: 4 }}
        />
      </label>

      <div style={{ fontSize: 12, marginTop: 16, color: "var(--text-secondary)" }}>
        <div>Status: {completionStatus}</div>
        <div>Shortcut: {mod}+Space (trigger), Tab (accept), Esc (reject)</div>
        <div style={{ marginTop: 8 }}>
          Telemetry: {telemetry.requested} requested, {telemetry.shown} shown,{" "}
          {telemetry.accepted} accepted, {telemetry.rejected} rejected
        </div>
      </div>
    </div>
  );
}
