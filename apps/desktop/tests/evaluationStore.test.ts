import { describe, expect, it, beforeEach } from "vitest";
import { useEvaluationStore } from "../src/renderer/src/state/evaluationStore";

describe("evaluationStore", () => {
  beforeEach(() => {
    useEvaluationStore.setState({
      benchmarks: [],
      runs: [],
      selectedBenchmark: null,
      running: false,
    });
  });

  it("tracks benchmark selection and runs", () => {
    useEvaluationStore.getState().setSelectedBenchmark("coding-mini");
    expect(useEvaluationStore.getState().selectedBenchmark).toBe("coding-mini");

    useEvaluationStore.getState().addRun({
      runId: "run-1",
      benchmarkId: "coding-mini",
      status: "completed",
      metrics: [{ metric_id: "code_pass_rate", value: 1.0 }],
      samples: 2,
    });
    expect(useEvaluationStore.getState().runs).toHaveLength(1);
  });
});
