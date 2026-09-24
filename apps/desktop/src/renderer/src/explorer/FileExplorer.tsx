import { useCallback, useEffect, useState } from "react";
import type { FileEntry } from "@shared/types";
import { useEditorStore } from "../state/editorStore";
import { useNotificationStore } from "../state/notificationStore";

function isError(v: unknown): boolean {
  return typeof v === "object" && v !== null && "code" in v;
}

export function FileExplorer() {
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set([""]));
  const [children, setChildren] = useState<Record<string, FileEntry[]>>({});
  const openTab = useEditorStore((s) => s.openTab);
  const notify = useNotificationStore((s) => s.notify);

  const loadDir = useCallback(async (path = "") => {
    const result = await window.desktop.files.list(path);
    if (isError(result)) {
      notify("error", (result as { message: string }).message);
      return;
    }
    if (path === "") {
      setEntries(result as FileEntry[]);
    } else {
      setChildren((prev) => ({ ...prev, [path]: result as FileEntry[] }));
    }
  }, [notify]);

  useEffect(() => {
    void loadDir();
    const unsub = window.desktop.files.onChanged(() => void loadDir());
    return unsub;
  }, [loadDir]);

  const openFile = async (path: string) => {
    const result = await window.desktop.files.read(path);
    if (isError(result)) {
      notify("error", (result as { message: string }).message);
      return;
    }
    const file = result as { path: string; content: string };
    openTab(file.path, file.content);
  };

  const toggleDir = async (path: string) => {
    const next = new Set(expanded);
    if (next.has(path)) {
      next.delete(path);
    } else {
      next.add(path);
      if (!children[path]) await loadDir(path);
    }
    setExpanded(next);
  };

  const renderEntry = (entry: FileEntry, depth = 0) => {
    const padding = 8 + depth * 12;
    if (entry.type === "directory") {
      const isOpen = expanded.has(entry.path);
      return (
        <div key={entry.path}>
          <div
            style={{ padding: `2px 8px 2px ${padding}px`, cursor: "pointer" }}
            onClick={() => toggleDir(entry.path)}
          >
            {isOpen ? "▼" : "▶"} {entry.name}
          </div>
          {isOpen &&
            (children[entry.path] ?? []).map((child) => renderEntry(child, depth + 1))}
        </div>
      );
    }
    return (
      <div
        key={entry.path}
        style={{ padding: `2px 8px 2px ${padding + 12}px`, cursor: "pointer" }}
        onClick={() => openFile(entry.path)}
      >
        {entry.name}
      </div>
    );
  };

  return (
    <div className="panel" style={{ height: "100%", overflow: "auto" }}>
      <div className="panel-header">Explorer</div>
      <div style={{ padding: 4 }}>{entries.map((e) => renderEntry(e))}</div>
    </div>
  );
}
