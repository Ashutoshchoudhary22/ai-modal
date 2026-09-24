import { useEffect, useState } from "react";
import { commandRegistry } from "../state/commands";

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const commands = commandRegistry.list().filter((c) =>
    c.title.toLowerCase().includes(query.toLowerCase()),
  );

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (open) window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.5)",
        display: "flex",
        justifyContent: "center",
        paddingTop: 80,
        zIndex: 200,
      }}
      onClick={onClose}
    >
      <div
        className="panel"
        style={{ width: 500, maxHeight: 400, overflow: "auto" }}
        onClick={(e) => e.stopPropagation()}
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type a command..."
          autoFocus
          style={{ width: "100%", padding: 12, border: "none", borderBottom: "1px solid var(--border)" }}
        />
        {commands.map((cmd) => (
          <div
            key={cmd.id}
            style={{ padding: "8px 12px", cursor: "pointer" }}
            onClick={() => {
              commandRegistry.execute(cmd.id);
              onClose();
            }}
          >
            {cmd.title}
            {cmd.shortcut && (
              <span style={{ float: "right", color: "var(--text-secondary)" }}>{cmd.shortcut}</span>
            )}
          </div>
        ))}
        {commands.length === 0 && (
          <div style={{ padding: 12, color: "var(--text-secondary)" }}>No matching commands</div>
        )}
      </div>
    </div>
  );
}
