import { useState } from "react";
import { useWorkspaceStore } from "../state/workspaceStore";
import { useSettingsStore } from "../state/settingsStore";
import { useEditorStore } from "../state/editorStore";
import { searchWorkspace, searchSymbols } from "../api/indexer";

interface SearchPanelProps {
  open: boolean;
  onClose: () => void;
}

export function SearchPanel({ open, onClose }: SearchPanelProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<string[]>([]);
  const [symbols, setSymbols] = useState<Array<{ name: string; path: string }>>([]);
  const workspace = useWorkspaceStore((s) => s.workspace);
  const settings = useSettingsStore((s) => s.settings);
  const openTab = useEditorStore((s) => s.openTab);

  const search = async () => {
    if (!query.trim()) return;
    if (workspace?.indexerWorkspaceId && settings) {
      try {
        const indexerResults = await searchWorkspace(
          settings.indexerUrl,
          workspace.indexerWorkspaceId,
          query,
        );
        setResults(indexerResults.map((r) => r.path));
        const symResults = await searchSymbols(
          settings.indexerUrl,
          workspace.indexerWorkspaceId,
          query,
        );
        setSymbols(symResults);
      } catch {
        const local = await window.desktop.files.search(query);
        if (Array.isArray(local)) setResults(local);
      }
    } else {
      const local = await window.desktop.files.search(query);
      if (Array.isArray(local)) setResults(local);
    }
  };

  const openFile = async (path: string) => {
    const result = await window.desktop.files.read(path);
    if (result && typeof result === "object" && "content" in result) {
      openTab(path, (result as { content: string }).content);
      onClose();
    }
  };

  if (!open) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.5)",
        display: "flex",
        justifyContent: "center",
        paddingTop: 60,
        zIndex: 200,
      }}
      onClick={onClose}
    >
      <div className="panel" style={{ width: 600, maxHeight: 500, overflow: "auto" }} onClick={(e) => e.stopPropagation()}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void search();
            if (e.key === "Escape") onClose();
          }}
          placeholder="Search workspace..."
          autoFocus
          style={{ width: "100%", padding: 12 }}
        />
        {symbols.length > 0 && (
          <div style={{ padding: 8 }}>
            <h4>Symbols</h4>
            {symbols.map((s) => (
              <div key={`${s.path}:${s.name}`} style={{ cursor: "pointer", padding: 2 }} onClick={() => void openFile(s.path)}>
                {s.name} — {s.path}
              </div>
            ))}
          </div>
        )}
        <div style={{ padding: 8 }}>
          {results.map((r) => (
            <div key={r} style={{ cursor: "pointer", padding: 2 }} onClick={() => void openFile(r)}>
              {r}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
