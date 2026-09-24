import { useEffect, useState } from "react";
import type { GitStatusResult } from "@shared/types";
import { useEditorStore } from "../state/editorStore";

function isError(v: unknown): boolean {
  return typeof v === "object" && v !== null && "code" in v;
}

export function GitPanel() {
  const [status, setStatus] = useState<GitStatusResult | null>(null);
  const [diff, setDiff] = useState<string>("");
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const openTab = useEditorStore((s) => s.openTab);

  const refresh = async () => {
    const result = await window.desktop.git.status();
    if (!isError(result)) setStatus(result as GitStatusResult);
  };

  useEffect(() => {
    void refresh();
  }, []);

  const showDiff = async (path: string) => {
    setSelectedFile(path);
    const result = await window.desktop.git.diff(path);
    if (!isError(result)) setDiff((result as { diff: string }).diff);
  };

  const openFile = async (path: string) => {
    const result = await window.desktop.files.read(path);
    if (!isError(result)) {
      const file = result as { path: string; content: string };
      openTab(file.path, file.content);
    }
  };

  if (!status) {
    return <div style={{ padding: 16, color: "var(--text-secondary)" }}>No Git repository</div>;
  }

  const allFiles = [
    ...status.modified.map((f) => ({ file: f, type: "M" })),
    ...status.added.map((f) => ({ file: f, type: "A" })),
    ...status.deleted.map((f) => ({ file: f, type: "D" })),
    ...status.untracked.map((f) => ({ file: f, type: "?" })),
  ];

  return (
    <div style={{ display: "flex", height: "100%" }}>
      <div style={{ width: 200, borderRight: "1px solid var(--border)", overflow: "auto", padding: 8 }}>
        <div style={{ marginBottom: 8, fontWeight: 600 }}>Branch: {status.branch ?? "—"}</div>
        <button onClick={() => void refresh()} style={{ marginBottom: 8 }}>Refresh</button>
        {allFiles.map(({ file, type }) => (
          <div
            key={file}
            style={{
              padding: "2px 4px",
              cursor: "pointer",
              background: selectedFile === file ? "var(--bg-tertiary)" : undefined,
            }}
            onClick={() => void showDiff(file)}
            onDoubleClick={() => void openFile(file)}
          >
            <span style={{ color: "var(--warning)", marginRight: 4 }}>{type}</span>
            {file}
          </div>
        ))}
        {allFiles.length === 0 && <div style={{ color: "var(--text-secondary)" }}>No changes</div>}
      </div>
      <pre style={{ flex: 1, overflow: "auto", padding: 8, fontSize: 11, fontFamily: "var(--font-mono)" }}>
        {diff || "Select a file to view diff"}
      </pre>
    </div>
  );
}
