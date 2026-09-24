import { create } from "zustand";
import type { TerminalSession } from "@shared/types";

interface TerminalState {
  id: string;
  session: TerminalSession;
}

interface TerminalStore {
  terminals: TerminalState[];
  activeTerminal: string | null;
  addTerminal: (session: TerminalSession) => void;
  removeTerminal: (id: string) => void;
  setActiveTerminal: (id: string) => void;
}

export const useTerminalStore = create<TerminalStore>((set) => ({
  terminals: [],
  activeTerminal: null,

  addTerminal: (session) =>
    set((state) => ({
      terminals: [...state.terminals, { id: session.id, session }],
      activeTerminal: session.id,
    })),

  removeTerminal: (id) =>
    set((state) => {
      const next = state.terminals.filter((t) => t.id !== id);
      return {
        terminals: next,
        activeTerminal:
          state.activeTerminal === id
            ? next[next.length - 1]?.id ?? null
            : state.activeTerminal,
      };
    }),

  setActiveTerminal: (id) => set({ activeTerminal: id }),
}));
