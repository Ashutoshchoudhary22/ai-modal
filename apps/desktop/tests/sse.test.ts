import { describe, expect, it, vi } from "vitest";
import { consumeSSE } from "../src/renderer/src/api/sse";

describe("SSE consumer", () => {
  it("parses SSE events", async () => {
    const events: Record<string, unknown>[] = [];
    const encoder = new TextEncoder();
    const body = 'data: {"type":"chunk","content":"hello"}\n\ndata: {"type":"done"}\n\n';

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: {
        getReader: () => {
          let done = false;
          return {
            read: async () => {
              if (done) return { done: true, value: undefined };
              done = true;
              return { done: false, value: encoder.encode(body) };
            },
          };
        },
      },
    });

    await consumeSSE(
      "http://localhost:8000/v1/chat/stream",
      { messages: [] },
      {
        onEvent: (e) => events.push(e),
        onError: () => {},
        onDone: () => {},
      },
    );

    expect(events).toHaveLength(2);
    expect(events[0].content).toBe("hello");
  });
});
