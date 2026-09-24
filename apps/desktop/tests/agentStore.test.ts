import { describe, expect, it, beforeEach } from "vitest";
import { useAgentStore } from "../src/renderer/src/state/agentStore";

describe("agentStore", () => {
  beforeEach(() => {
    useAgentStore.setState({
      events: [],
      runs: [],
      running: false,
      pendingApproval: null,
      abortController: null,
    });
  });

  it("records agent events", () => {
    useAgentStore.getState().addEvent({ type: "tool_call", message: "file.read" });
    expect(useAgentStore.getState().events).toHaveLength(1);
  });

  it("tracks pending approval", () => {
    useAgentStore.getState().setPendingApproval({
      tool: "file.write",
      args: { path: "test.ts" },
    });
    expect(useAgentStore.getState().pendingApproval?.tool).toBe("file.write");
  });
});
