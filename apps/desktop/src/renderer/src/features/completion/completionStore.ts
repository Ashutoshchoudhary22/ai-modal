import { create } from "zustand";
import type { CompletionStatus, CompletionTelemetry } from "./completionTypes";

interface CompletionStore {
  enabled: boolean;
  status: CompletionStatus;
  loading: boolean;
  currentCompletion: string | null;
  requestId: string | null;
  documentVersion: number;
  cursorKey: string | null;
  filePath: string | null;
  error: string | null;
  lastLatencyMs: number | null;
  telemetry: CompletionTelemetry;
  setEnabled: (enabled: boolean) => void;
  setStatus: (status: CompletionStatus) => void;
  setLoading: (loading: boolean) => void;
  setCompletion: (text: string | null, requestId: string, cursorKey: string, filePath: string) => void;
  clearCompletion: () => void;
  setError: (error: string | null) => void;
  setLatency: (ms: number) => void;
  incrementTelemetry: (key: keyof CompletionTelemetry) => void;
}

export const useCompletionStore = create<CompletionStore>((set) => ({
  enabled: true,
  status: "ready",
  loading: false,
  currentCompletion: null,
  requestId: null,
  documentVersion: 0,
  cursorKey: null,
  filePath: null,
  error: null,
  lastLatencyMs: null,
  telemetry: {
    requested: 0,
    shown: 0,
    accepted: 0,
    rejected: 0,
    cancelled: 0,
    stale: 0,
    errors: 0,
  },

  setEnabled: (enabled) => set({ enabled, status: enabled ? "ready" : "disabled" }),
  setStatus: (status) => set({ status }),
  setLoading: (loading) =>
    set((state) => ({
      loading,
      ...(loading
        ? { status: "generating" as CompletionStatus }
        : state.status === "generating"
          ? { status: "ready" as CompletionStatus }
          : {}),
    })),
  setCompletion: (text, requestId, cursorKey, filePath) =>
    set({
      currentCompletion: text,
      requestId,
      cursorKey,
      filePath,
      loading: false,
      status: "ready",
    }),
  clearCompletion: () =>
    set({
      currentCompletion: null,
      requestId: null,
      cursorKey: null,
      filePath: null,
      loading: false,
    }),
  setError: (error) => set({ error, status: error ? "error" : "ready", loading: false }),
  setLatency: (ms) => set({ lastLatencyMs: ms }),
  incrementTelemetry: (key) =>
    set((state) => ({
      telemetry: { ...state.telemetry, [key]: state.telemetry[key] + 1 },
    })),
}));
