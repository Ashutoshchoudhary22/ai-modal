import DiffEditor from "@monaco-editor/react";
import { useEditorStore } from "../state/editorStore";

export function DiffReview() {
  const proposedChanges = useEditorStore((s) => s.proposedChanges);
  const reviewIndex = useEditorStore((s) => s.reviewIndex);
  const acceptChange = useEditorStore((s) => s.acceptChange);
  const rejectChange = useEditorStore((s) => s.rejectChange);
  const openTab = useEditorStore((s) => s.openTab);
  const updateContent = useEditorStore((s) => s.updateContent);

  if (proposedChanges.length === 0) return null;

  const change = proposedChanges[reviewIndex] ?? proposedChanges[0];

  const handleAccept = async () => {
    const accepted = acceptChange(reviewIndex);
    if (!accepted) return;
    openTab(accepted.path, accepted.modified);
    updateContent(accepted.path, accepted.modified);
    const result = await window.desktop.files.write(accepted.path, accepted.modified);
    if (result && typeof result === "object" && "code" in result) {
      /* error handled elsewhere */
    }
  };

  return (
    <div className="panel" style={{ position: "absolute", inset: 0, zIndex: 50, background: "var(--bg-primary)" }}>
      <div className="panel-header" style={{ display: "flex", justifyContent: "space-between" }}>
        <span>AI Proposed Change — {change.path} ({reviewIndex + 1}/{proposedChanges.length})</span>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => rejectChange(reviewIndex)}>Reject</button>
          <button className="primary" onClick={() => void handleAccept()}>Accept</button>
        </div>
      </div>
      <DiffEditor
        height="calc(100% - 32px)"
        original={change.original}
        modified={change.modified}
        language="typescript"
        theme="vs-dark"
        options={{ readOnly: true, renderSideBySide: true }}
      />
    </div>
  );
}
