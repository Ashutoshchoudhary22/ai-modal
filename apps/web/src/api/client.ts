export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export interface ReadyResponse {
  status: string;
  provider: string;
  provider_state: string;
  model_id: string | null;
  message: string | null;
}

export interface GenerateResponse {
  id: string;
  model: string;
  content: string;
  provider?: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface EmbedResponse {
  model: string;
  embeddings: number[][];
  dimensions: number;
  provider?: string;
}

export interface ModelsResponse {
  provider: string;
  provider_state: string;
  models: Array<Record<string, unknown>>;
}

const trimUrl = (url: string) => url.replace(/\/+$/, "");

export async function fetchHealth(baseUrl: string): Promise<HealthResponse> {
  const res = await fetch(`${trimUrl(baseUrl)}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchReady(baseUrl: string): Promise<ReadyResponse> {
  const res = await fetch(`${trimUrl(baseUrl)}/ready`);
  if (!res.ok) throw new Error(`Ready check failed: ${res.status}`);
  return res.json();
}

export async function fetchModels(baseUrl: string): Promise<ModelsResponse> {
  const res = await fetch(`${trimUrl(baseUrl)}/v1/models`);
  if (!res.ok) throw new Error(`Models request failed: ${res.status}`);
  return res.json();
}

export async function chat(
  baseUrl: string,
  messages: ChatMessage[],
  options: { maxTokens: number; temperature: number; stream: boolean },
): Promise<GenerateResponse | AsyncGenerator<string, void, unknown>> {
  const endpoint = options.stream ? "/v1/chat/stream" : "/v1/chat";
  const res = await fetch(`${trimUrl(baseUrl)}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages,
      max_tokens: options.maxTokens,
      temperature: options.temperature,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `Chat failed: ${res.status}`);
  }

  if (!options.stream) {
    return res.json();
  }

  if (!res.body) throw new Error("Streaming not supported by browser response");

  async function* streamText(): AsyncGenerator<string, void, unknown> {
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6).trim();
        if (!payload) continue;
        try {
          const chunk = JSON.parse(payload) as {
            type: string;
            content?: string;
            message?: string;
          };
          if (chunk.type === "chunk" && chunk.content) {
            yield chunk.content;
          }
          if (chunk.type === "error") {
            throw new Error(chunk.message ?? "Stream error");
          }
        } catch (error) {
          if (error instanceof SyntaxError) continue;
          throw error;
        }
      }
    }
  }

  return streamText();
}

export async function embed(baseUrl: string, inputs: string[]): Promise<EmbedResponse> {
  const res = await fetch(`${trimUrl(baseUrl)}/v1/embeddings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ inputs }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `Embeddings failed: ${res.status}`);
  }
  return res.json();
}
