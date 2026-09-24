import { create } from "zustand";

export interface EditorTab {
  path: string;
  content: string;
  dirty: boolean;
  language: string;
}

export interface ProposedChange {
  path: string;
  original: string;
  modified: string;
  source: "agent" | "ai" | "ui" | "screenshot";
}

interface EditorStore {
  tabs: EditorTab[];
  activeTab: string | null;
  untitledCounter: number;
  selection: { start: number; end: number; text: string } | null;
  proposedChanges: ProposedChange[];
  reviewIndex: number;
  openTab: (path: string, content: string, language?: string) => void;
  newUntitled: () => void;
  closeTab: (path: string) => void;
  setActiveTab: (path: string) => void;
  updateContent: (path: string, content: string) => void;
  markClean: (path: string) => void;
  setSelection: (sel: EditorStore["selection"]) => void;
  addProposedChange: (change: ProposedChange) => void;
  clearProposedChanges: () => void;
  setReviewIndex: (index: number) => void;
  acceptChange: (index: number) => ProposedChange | null;
  rejectChange: (index: number) => void;
  resetWorkspace: () => void;
}

function detectLanguage(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase();
  const map: Record<string, string> = {
    ts: "typescript",
    tsx: "typescript",
    js: "javascript",
    jsx: "javascript",
    py: "python",
    json: "json",
    md: "markdown",
    html: "html",
    css: "css",
    yaml: "yaml",
    yml: "yaml",
  };
  return map[ext ?? ""] ?? "plaintext";
}

export function isUntitledPath(path: string): boolean {
  return path.startsWith("untitled:");
}

export const useEditorStore = create<EditorStore>((set, get) => ({
  tabs: [],
  activeTab: null,
  untitledCounter: 0,
  selection: null,
  proposedChanges: [],
  reviewIndex: 0,

  openTab: (path, content, language) =>
    set((state) => {
      const existing = state.tabs.find((t) => t.path === path);
      if (existing) return { activeTab: path };
      return {
        tabs: [
          ...state.tabs,
          { path, content, dirty: false, language: language ?? detectLanguage(path) },
        ],
        activeTab: path,
      };
    }),

  newUntitled: () =>
    set((state) => {
      const next = state.untitledCounter + 1;
      const path = `untitled:${next}`;
      return {
        untitledCounter: next,
        tabs: [
          ...state.tabs,
          { path, content: "", dirty: false, language: "plaintext" },
        ],
        activeTab: path,
      };
    }),

  closeTab: (path) =>
    set((state) => {
      const tabs = state.tabs.filter((t) => t.path !== path);
      const activeTab =
        state.activeTab === path ? (tabs[tabs.length - 1]?.path ?? null) : state.activeTab;
      return { tabs, activeTab };
    }),

  setActiveTab: (path) => set({ activeTab: path }),

  updateContent: (path, content) =>
    set((state) => ({
      tabs: state.tabs.map((t) =>
        t.path === path ? { ...t, content, dirty: t.content !== content } : t,
      ),
    })),

  markClean: (path) =>
    set((state) => ({
      tabs: state.tabs.map((t) => (t.path === path ? { ...t, dirty: false } : t)),
    })),

  setSelection: (sel) => set({ selection: sel }),

  addProposedChange: (change) =>
    set((state) => ({
      proposedChanges: [...state.proposedChanges, change],
      reviewIndex: state.proposedChanges.length,
    })),

  clearProposedChanges: () => set({ proposedChanges: [], reviewIndex: 0 }),

  setReviewIndex: (index) => set({ reviewIndex: index }),

  acceptChange: (index) => {
    const change = get().proposedChanges[index];
    if (!change) return null;
    set((state) => ({
      proposedChanges: state.proposedChanges.filter((_, i) => i !== index),
      reviewIndex: Math.max(0, index - 1),
    }));
    return change;
  },

  rejectChange: (index) =>
    set((state) => ({
      proposedChanges: state.proposedChanges.filter((_, i) => i !== index),
      reviewIndex: Math.max(0, index - 1),
    })),

  resetWorkspace: () =>
    set({
      tabs: [],
      activeTab: null,
      untitledCounter: 0,
      selection: null,
      proposedChanges: [],
      reviewIndex: 0,
    }),
}));
