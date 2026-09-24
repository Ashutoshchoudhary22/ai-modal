import type { ApiHealthStatus } from "@shared/types";
import { consumeSSE } from "./sse";

const trim = (url: string) => url.replace(/\/+$/, "");

export interface HealthResponse {
  status: string;
  version?: string;
}

export interface ReadyResponse {
  status: string;
  provider: string;
  provider_state: string;
  model_id: string | null;
}

export interface ModelsResponse {
  provider: string;
  provider_state: string;
  models: Array<Record<string, unknown>>;
}

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export async function checkHealth(baseUrl: string): Promise<{
  health: HealthResponse;
  ready: ReadyResponse | null;
  status: ApiHealthStatus;
}> {
  try {
    const healthRes = await fetch(`${trim(baseUrl)}/health`);
    if (!healthRes.ok) return { health: { status: "error" }, ready: null, status: "error" };
    const health = (await healthRes.json()) as HealthResponse;
    let ready: ReadyResponse | null = null;
    try {
      const readyRes = await fetch(`${trim(baseUrl)}/ready`);
      if (readyRes.ok) ready = (await readyRes.json()) as ReadyResponse;
    } catch {
      /* optional */
    }
    return { health, ready, status: "connected" };
  } catch {
    return { health: { status: "error" }, ready: null, status: "disconnected" };
  }
}

export async function fetchModels(baseUrl: string): Promise<ModelsResponse> {
  const res = await fetch(`${trim(baseUrl)}/v1/models`);
  if (!res.ok) throw new Error(`Models request failed: ${res.status}`);
  return res.json();
}

export async function streamChat(
  baseUrl: string,
  messages: ChatMessage[],
  options: { maxTokens: number; temperature: number; model?: string },
  onChunk: (text: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  await consumeSSE(
    `${trim(baseUrl)}/v1/chat/stream`,
    {
      messages,
      max_tokens: options.maxTokens,
      temperature: options.temperature,
      model: options.model,
    },
    {
      onEvent: (event) => {
        if (event.type === "chunk" && typeof event.content === "string") {
          onChunk(event.content);
        }
        if (event.type === "error") {
          throw new Error(String(event.message ?? "Stream error"));
        }
      },
      onError: (err) => {
        throw err;
      },
      onDone: () => {},
    },
    signal,
  );
}
