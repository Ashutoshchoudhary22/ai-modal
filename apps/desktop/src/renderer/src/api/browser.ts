import { consumeSSE } from "./sse";

const trim = (url: string) => url.replace(/\/+$/, "");

export async function streamBrowserRun(
  agentUrl: string,
  body: {
    workspace_id: string;
    task: string;
    start_url: string;
    allowed_domains: string[];
    root_path?: string;
  },
  onEvent: (event: Record<string, unknown>) => void,
  signal?: AbortSignal,
): Promise<void> {
  await consumeSSE(
    `${trim(agentUrl)}/v1/browser/runs/stream`,
    body,
    {
      onEvent,
      onError: (err) => {
        throw err;
      },
      onDone: () => {},
    },
    signal,
  );
}
