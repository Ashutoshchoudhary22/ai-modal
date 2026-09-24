import { create } from "zustand";

export interface AgentEvent {
  id: string;
  type: string;
  message: string;
  timestamp: string;
}

export interface AgentRun {
  id: string;
  task: string;
  status: "running" | "completed" | "failed" | "cancelled";
  startedAt: string;
  durationMs: number | null;
  filesChanged: number;
}

interface AgentStore {
  events: AgentEvent[];
  runs: AgentRun[];
  running: boolean;
  pendingApproval: { tool: string; args: Record<string, unknown> } | null;
  abortController: AbortController | null;
  addEvent: (event: Omit<AgentEvent, "id" | "timestamp">) => void;
  clearEvents: () => void;
  addRun: (run: AgentRun) => void;
  updateRun: (id: string, update: Partial<AgentRun>) => void;
  setRunning: (running: boolean) => void;
  setPendingApproval: (approval: AgentStore["pendingApproval"]) => void;
  setAbortController: (controller: AbortController | null) => void;
}

let eventCounter = 0;

export const useAgentStore = create<AgentStore>((set) => ({
  events: [],
  runs: [],
  running: false,
  pendingApproval: null,
  abortController: null,

  addEvent: (event) =>
    set((state) => ({
      events: [
        ...state.events,
        {
          ...event,
          id: `evt-${++eventCounter}`,
          timestamp: new Date().toISOString(),
        },
      ],
    })),

  clearEvents: () => set({ events: [] }),

  addRun: (run) => set((state) => ({ runs: [run, ...state.runs].slice(0, 20) })),

  updateRun: (id, update) =>
    set((state) => ({
      runs: state.runs.map((r) => (r.id === id ? { ...r, ...update } : r)),
    })),

  setRunning: (running) => set({ running }),

  setPendingApproval: (approval) => set({ pendingApproval: approval }),

  setAbortController: (controller) => set({ abortController: controller }),
}));
