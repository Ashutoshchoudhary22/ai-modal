import type {
  CompletionRequestPayload,
  CompletionResponsePayload,
} from "../features/completion/completionTypes";

const trim = (url: string) => url.replace(/\/+$/, "");

export async function requestCompletion(
  baseUrl: string,
  payload: CompletionRequestPayload,
  signal?: AbortSignal,
): Promise<CompletionResponsePayload> {
  const res = await fetch(`${trim(baseUrl)}/v1/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  if (!res.ok) {
    const text = await res.text();
    let message = text;
    try {
      const parsed = JSON.parse(text) as { detail?: { message?: string } };
      message = parsed.detail?.message ?? text;
    } catch {
      /* use raw */
    }
    throw new Error(message || `Completion failed: ${res.status}`);
  }
  return res.json();
}
