import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CompletionController } from "../src/renderer/src/features/completion/CompletionController";
import { useCompletionStore } from "../src/renderer/src/features/completion/completionStore";
import { requestCompletion } from "../src/renderer/src/api/completion";

vi.mock("../src/renderer/src/api/completion", () => ({
  requestCompletion: vi.fn(async () => ({
    request_id: "test",
    completion: { text: "findById(id);" },
    latency_ms: 1,
  })),
}));

const baseSettings = {
  apiUrl: "http://127.0.0.1:8000",
  indexerUrl: "http://127.0.0.1:8002",
  indexerWorkspaceId: null,
  enabled: true,
  model: "development-mock-v1",
  debounceMs: 10,
  maxTokens: 64,
  contextLines: 10,
  repositoryContextEnabled: false,
  maxRequestsPerMinute: 60,
  timeoutMs: 5000,
  triggerOnTyping: true,
};

const snapshot = {
  filePath: "src/example.ts",
  language: "typescript",
  content: "const user = await db.",
  line: 0,
  column: 22,
  offset: 22,
  documentVersion: 1,
};

describe("CompletionController", () => {
  beforeEach(() => {
    vi.useRealTimers();
    useCompletionStore.setState({
      enabled: true,
      status: "ready",
      loading: false,
      currentCompletion: null,
      requestId: null,
      documentVersion: 0,
      cursorKey: null,
      filePath: null,
      error: null,
      lastLatencyMs: null,
      telemetry: {
        requested: 0,
        shown: 0,
        accepted: 0,
        rejected: 0,
        cancelled: 0,
        stale: 0,
        errors: 0,
      },
    });
    vi.mocked(requestCompletion).mockResolvedValue({
      request_id: "test",
      completion: { text: "findById(id);" },
      latency_ms: 1,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("discards stale responses after invalidation", async () => {
    vi.mocked(requestCompletion).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(
            () =>
              resolve({
                request_id: "test",
                completion: { text: "findById(id);" },
                latency_ms: 1,
              }),
            30,
          );
        }),
    );

    const controller = new CompletionController(() => baseSettings);
    const promise = controller.provide(snapshot, "automatic");
    await new Promise((r) => setTimeout(r, 15));
    controller.invalidate("content");
    const result = await promise;
    expect(result).toBeNull();
    expect(useCompletionStore.getState().telemetry.stale).toBeGreaterThan(0);
    controller.dispose();
  });

  it("suppresses automatic completion during post-accept cooldown", async () => {
    const controller = new CompletionController(() => baseSettings);
    controller.acceptCompletion();
    const result = await controller.provide(snapshot, "automatic");
    expect(result).toBeNull();
    controller.dispose();
  });

  it("discards response when cursor invalidation generation changes", async () => {
    vi.mocked(requestCompletion).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(
            () =>
              resolve({
                request_id: "test",
                completion: { text: "findById(id);" },
                latency_ms: 1,
              }),
            30,
          );
        }),
    );
    const controller = new CompletionController(() => baseSettings);
    const promise = controller.provide(snapshot, "automatic");
    await new Promise((r) => setTimeout(r, 15));
    controller.invalidate("cursor");
    const result = await promise;
    expect(result).toBeNull();
    controller.dispose();
  });

  it("allows explicit manual completion when typing trigger is disabled", async () => {
    const controller = new CompletionController(() => ({
      ...baseSettings,
      triggerOnTyping: false,
    }));

    const result = await controller.provide(snapshot, "manual");
    expect(result).toBe("findById(id);");
    controller.dispose();
  });
});
