import { consumeSSE } from "./sse";

const trim = (url: string) => url.replace(/\/+$/, "");

export async function streamUIGenerate(
  agentUrl: string,
  body: {
    workspace_id: string;
    request: string;
    root_path: string;
  },
  onEvent: (event: Record<string, unknown>) => void,
  signal?: AbortSignal,
): Promise<void> {
  await consumeSSE(
    `${trim(agentUrl)}/v1/ui/generate/stream`,
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

export async function streamScreenshotToCode(
  agentUrl: string,
  body: {
    workspace_id: string;
    root_path: string;
    image_base64: string;
    mime_type: string;
  },
  onEvent: (event: Record<string, unknown>) => void,
  signal?: AbortSignal,
): Promise<void> {
  await consumeSSE(
    `${trim(agentUrl)}/v1/ui/screenshot-to-code/stream`,
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
