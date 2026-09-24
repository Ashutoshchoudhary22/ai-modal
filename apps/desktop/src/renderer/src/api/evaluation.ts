import { consumeSSE } from "./sse";

const trim = (url: string) => url.replace(/\/+$/, "");

export interface BenchmarkInfo {
  benchmark_id: string;
  name: string;
  version: string;
  task_type: string;
  metrics: string[];
}

export interface EvaluationRunResult {
  run_id: string;
  status: string;
  error?: string;
}

export async function listBenchmarks(agentUrl: string): Promise<BenchmarkInfo[]> {
  const res = await fetch(`${trim(agentUrl)}/v1/evaluations/benchmarks`);
  if (!res.ok) throw new Error(`Benchmarks request failed: ${res.status}`);
  return res.json();
}

export async function createEvaluationRun(
  agentUrl: string,
  body: {
    benchmark_id: string;
    model_id?: string;
    model_provider?: string;
    dry_run?: boolean;
  },
): Promise<EvaluationRunResult> {
  const res = await fetch(`${trim(agentUrl)}/v1/evaluations/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Evaluation run failed: ${res.status}`);
  }
  return res.json();
}

export async function getEvaluationRun(
  agentUrl: string,
  runId: string,
): Promise<Record<string, unknown>> {
  const res = await fetch(`${trim(agentUrl)}/v1/evaluations/runs/${runId}`);
  if (!res.ok) throw new Error(`Evaluation status failed: ${res.status}`);
  return res.json();
}

export async function cancelEvaluationRun(agentUrl: string, runId: string): Promise<void> {
  const res = await fetch(`${trim(agentUrl)}/v1/evaluations/runs/${runId}/cancel`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Cancel failed: ${res.status}`);
}
