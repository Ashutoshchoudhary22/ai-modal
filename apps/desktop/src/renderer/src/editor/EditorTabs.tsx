import { useEditorStore } from "../state/editorStore";
import { useNotificationStore } from "../state/notificationStore";

function isError(v: unknown): boolean {
  return typeof v === "object" && v !== null && "code" in v;
}

export function EditorTabs() {
  const tabs = useEditorStore((s) => s.tabs);
  const activeTab = useEditorStore((s) => s.activeTab);
  const setActiveTab = useEditorStore((s) => s.setActiveTab);
  const closeTab = useEditorStore((s) => s.closeTab);
  const markClean = useEditorStore((s) => s.markClean);
  const notify = useNotificationStore((s) => s.notify);

  const saveTab = async (path: string) => {
    const tab = tabs.find((t) => t.path === path);
    if (!tab) return;
    const result = await window.desktop.files.write(path, tab.content);
    if (isError(result)) {
      notify("error", (result as { message: string }).message);
      return;
    }
    markClean(path);
    notify("success", `Saved ${path}`);
  };

  const handleClose = async (path: string) => {
    const tab = tabs.find((t) => t.path === path);
    if (tab?.dirty) {
      const action = window.confirm(`Save changes to ${path}?`);
      if (action) await saveTab(path);
    }
    closeTab(path);
  };

  if (tabs.length === 0) return null;

  return (
    <div style={{ display: "flex", borderBottom: "1px solid var(--border)", background: "var(--bg-tertiary)" }}>
      {tabs.map((tab) => (
        <div
          key={tab.path}
          onClick={() => setActiveTab(tab.path)}
          style={{
            padding: "6px 12px",
            cursor: "pointer",
            borderRight: "1px solid var(--border)",
            background: activeTab === tab.path ? "var(--bg-primary)" : "transparent",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span>{tab.dirty ? "● " : ""}{tab.path.split("/").pop()}</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              void handleClose(tab.path);
            }}
            style={{ padding: "0 4px", fontSize: 10 }}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
