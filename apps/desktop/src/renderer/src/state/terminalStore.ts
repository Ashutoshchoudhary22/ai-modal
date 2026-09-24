import { create } from "zustand";
import type { TerminalSession } from "@shared/types";

export interface TerminalLine {
  type: "stdout" | "stderr" | "input" | "error";
  text: string;
}

interface TerminalState {
  id: string;
  session: TerminalSession;
  lines: TerminalLine[];
}

interface TerminalStore {
  terminals: TerminalState[];
  activeTerminal: string | null;
  addTerminal: (session: TerminalSession) => void;
  removeTerminal: (id: string) => void;
  setActiveTerminal: (id: string) => void;
  appendLine: (id: string, line: TerminalLine) => void;
  clearLines: (id: string) => void;
}

const MAX_LINES = 500;

export const useTerminalStore = create<TerminalStore>((set) => ({
  terminals: [],
  activeTerminal: null,

  addTerminal: (session) =>
    set((state) => ({
      terminals: [...state.terminals, { id: session.id, session, lines: [] }],
      activeTerminal: session.id,
    })),

  removeTerminal: (id) =>
    set((state) => ({
      terminals: state.terminals.filter((t) => t.id !== id),
      activeTerminal: state.activeTerminal === id ? null : state.activeTerminal,
    })),

  setActiveTerminal: (id) => set({ activeTerminal: id }),

  appendLine: (id, line) =>
    set((state) => ({
      terminals: state.terminals.map((t) =>
        t.id === id
          ? { ...t, lines: [...t.lines, line].slice(-MAX_LINES) }
          : t,
      ),
    })),

  clearLines: (id) =>
    set((state) => ({
      terminals: state.terminals.map((t) => (t.id === id ? { ...t, lines: [] } : t)),
    })),
}));
