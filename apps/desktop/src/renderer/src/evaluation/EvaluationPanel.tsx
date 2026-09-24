import { useEffect } from "react";
import { useEvaluationStore } from "../state/evaluationStore";
import { useSettingsStore } from "../state/settingsStore";
import { useNotificationStore } from "../state/notificationStore";
import { listBenchmarks, createEvaluationRun } from "../api/evaluation";

export function EvaluationPanel() {
  const benchmarks = useEvaluationStore((s) => s.benchmarks);
  const runs = useEvaluationStore((s) => s.runs);
  const selectedBenchmark = useEvaluationStore((s) => s.selectedBenchmark);
  const running = useEvaluationStore((s) => s.running);
  const settings = useSettingsStore((s) => s.settings);
  const notify = useNotificationStore((s) => s.notify);

  useEffect(() => {
    if (!settings) return;
    void listBenchmarks(settings.agentUrl)
      .then((list) => useEvaluationStore.getState().setBenchmarks(list))
      .catch(() => notify("error", "Failed to load benchmarks"));
  }, [settings, notify]);

  const runBenchmark = async (dryRun = false) => {
    if (!settings || !selectedBenchmark) return;
    useEvaluationStore.getState().setRunning(true);
    try {
      const result = await createEvaluationRun(settings.agentUrl, {
        benchmark_id: selectedBenchmark,
        model_provider: "development_mock",
        dry_run: dryRun,
      });
      useEvaluationStore.getState().addRun({
        runId: result.run_id,
        benchmarkId: selectedBenchmark,
        status: result.status,
        metrics: [],
        samples: 0,
        error: result.error,
      });
      notify("success", dryRun ? "Dry run complete" : `Evaluation ${result.status}`);
    } catch (err) {
      notify("error", err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      useEvaluationStore.getState().setRunning(false);
    }
  };

  return (
    <div style={{ padding: 12, height: "100%", overflow: "auto" }}>
      <h3 style={{ marginBottom: 8 }}>Evaluation</h3>
      <div style={{ marginBottom: 12 }}>
        <select
          value={selectedBenchmark ?? ""}
          onChange={(e) => useEvaluationStore.getState().setSelectedBenchmark(e.target.value || null)}
          style={{ width: "100%", marginBottom: 8 }}
        >
          <option value="">Select benchmark...</option>
          {benchmarks.map((b) => (
            <option key={b.benchmark_id} value={b.benchmark_id}>
              {b.name} ({b.task_type})
            </option>
          ))}
        </select>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => void runBenchmark(true)} disabled={!selectedBenchmark || running}>
            Dry Run
          </button>
          <button className="primary" onClick={() => void runBenchmark(false)} disabled={!selectedBenchmark || running}>
            Run
          </button>
        </div>
      </div>
      <h4 style={{ marginBottom: 4 }}>Recent Runs</h4>
      {runs.length === 0 && <div style={{ color: "var(--text-secondary)" }}>No evaluation runs</div>}
      {runs.map((run) => (
        <div key={run.runId} style={{ padding: 8, borderBottom: "1px solid var(--border)", fontSize: 12 }}>
          <div><strong>{run.benchmarkId}</strong> — {run.status}</div>
          <div style={{ color: "var(--text-secondary)" }}>Run ID: {run.runId}</div>
          {run.error && <div style={{ color: "var(--error)" }}>{run.error}</div>}
        </div>
      ))}
    </div>
  );
}
