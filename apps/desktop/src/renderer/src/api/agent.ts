import { consumeSSE } from "./sse";

const trim = (url: string) => url.replace(/\/+$/, "");

export interface AgentRunRequest {
  workspace_id: string;
  task: string;
  root_path: string;
  policy?: string;
  max_iterations?: number;
  model_id?: string;
}

export interface AgentEvent {
  type: string;
  [key: string]: unknown;
}

export async function streamAgentRun(
  agentUrl: string,
  request: AgentRunRequest,
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  await consumeSSE(
    `${trim(agentUrl)}/v1/agent/runs/stream`,
    request,
    {
      onEvent: (event) => onEvent(event as AgentEvent),
      onError: (err) => {
        throw err;
      },
      onDone: () => {},
    },
    signal,
  );
}

export async function executeTool(
  agentUrl: string,
  body: {
    workspace_id: string;
    tool_name: string;
    arguments: Record<string, unknown>;
    root_path: string;
  },
): Promise<Record<string, unknown>> {
  const res = await fetch(`${trim(agentUrl)}/v1/tools/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Tool execution failed: ${res.status}`);
  }
  return res.json();
}
