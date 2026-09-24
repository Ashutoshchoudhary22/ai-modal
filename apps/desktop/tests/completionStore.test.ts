import { describe, expect, it, beforeEach } from "vitest";
import { useCompletionStore } from "../src/renderer/src/features/completion/completionStore";

describe("completionStore", () => {
  beforeEach(() => {
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
  });

  it("tracks completion state", () => {
    useCompletionStore.getState().setCompletion("findById(id);", "req-1", "key", "src/a.ts");
    expect(useCompletionStore.getState().currentCompletion).toBe("findById(id);");
    useCompletionStore.getState().clearCompletion();
    expect(useCompletionStore.getState().currentCompletion).toBeNull();
  });

  it("tracks telemetry", () => {
    useCompletionStore.getState().incrementTelemetry("accepted");
    expect(useCompletionStore.getState().telemetry.accepted).toBe(1);
  });
});
