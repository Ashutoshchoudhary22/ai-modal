import { create } from "zustand";
import type { BenchmarkInfo } from "../api/evaluation";

export interface EvaluationRunState {
  runId: string;
  benchmarkId: string;
  status: string;
  metrics: Array<{ metric_id: string; value: number | null }>;
  samples: number;
  error?: string;
}

interface EvaluationStore {
  benchmarks: BenchmarkInfo[];
  runs: EvaluationRunState[];
  selectedBenchmark: string | null;
  running: boolean;
  setBenchmarks: (benchmarks: BenchmarkInfo[]) => void;
  setSelectedBenchmark: (id: string | null) => void;
  addRun: (run: EvaluationRunState) => void;
  updateRun: (runId: string, update: Partial<EvaluationRunState>) => void;
  setRunning: (running: boolean) => void;
}

export const useEvaluationStore = create<EvaluationStore>((set) => ({
  benchmarks: [],
  runs: [],
  selectedBenchmark: null,
  running: false,

  setBenchmarks: (benchmarks) => set({ benchmarks }),
  setSelectedBenchmark: (id) => set({ selectedBenchmark: id }),
  addRun: (run) => set((state) => ({ runs: [run, ...state.runs] })),
  updateRun: (runId, update) =>
    set((state) => ({
      runs: state.runs.map((r) => (r.runId === runId ? { ...r, ...update } : r)),
    })),
  setRunning: (running) => set({ running }),
}));
