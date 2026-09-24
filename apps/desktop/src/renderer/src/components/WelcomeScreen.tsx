import { useWorkspaceStore } from "../state/workspaceStore";
import { useSettingsStore } from "../state/settingsStore";

export function WelcomeScreen() {
  const recents = useWorkspaceStore((s) => s.recents);
  const { apiStatus, provider, modelId } = useSettingsStore();

  const openFolder = async () => {
    const result = await window.desktop.workspace.open();
    if (result && "rootPath" in result) {
      useWorkspaceStore.getState().setWorkspace(result);
      const info = await window.desktop.workspace.getProjectInfo();
      useWorkspaceStore.getState().setProjectInfo(info);
    }
  };

  const openRecent = async (path: string) => {
    const result = await window.desktop.workspace.openPath(path);
    if (result && "rootPath" in result) {
      useWorkspaceStore.getState().setWorkspace(result);
      const info = await window.desktop.workspace.getProjectInfo();
      useWorkspaceStore.getState().setProjectInfo(info);
    }
  };

  return (
    <div className="welcome" style={{ padding: 48, textAlign: "center" }}>
      <h1 style={{ fontSize: 28, marginBottom: 8 }}>AI Platform IDE</h1>
      <p style={{ color: "var(--text-secondary)", marginBottom: 32 }}>
        Open a workspace to start coding with AI assistance
      </p>
      <button className="primary" onClick={openFolder} style={{ padding: "10px 24px", fontSize: 14 }}>
        Open Folder
      </button>
      <div style={{ marginTop: 32, textAlign: "left", maxWidth: 400, margin: "32px auto" }}>
        <div style={{ marginBottom: 16 }}>
          <span className={`status-dot ${apiStatus}`} /> AI Service: {apiStatus}
          {provider && (
            <span style={{ marginLeft: 12, color: "var(--text-secondary)" }}>
              {provider} / {modelId ?? "default"}
            </span>
          )}
        </div>
        {recents.length > 0 && (
          <div>
            <h3 style={{ fontSize: 12, textTransform: "uppercase", marginBottom: 8 }}>Recent Projects</h3>
            {recents.map((r) => (
              <button
                key={r.rootPath}
                onClick={() => openRecent(r.rootPath)}
                style={{ display: "block", width: "100%", textAlign: "left", marginBottom: 4 }}
              >
                {r.name}
                <span style={{ color: "var(--text-secondary)", fontSize: 11, marginLeft: 8 }}>
                  {r.rootPath}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
