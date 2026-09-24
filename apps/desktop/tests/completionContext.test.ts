import { describe, expect, it } from "vitest";
import { collectCompletionContext } from "../src/renderer/src/features/completion/CompletionContextCollector";

describe("CompletionContextCollector", () => {
  it("uses unsaved editor buffer content instead of disk", () => {
    const snapshot = {
      filePath: "src/unsaved.ts",
      language: "typescript",
      content: "const user = await db.",
      line: 0,
      column: 22,
      offset: 22,
      documentVersion: 3,
    };
    const { prefix, suffix } = collectCompletionContext(snapshot, 10);
    expect(prefix).toBe("const user = await db.");
    expect(suffix).toBe("");
    expect(prefix).not.toContain("DISK_VERSION");
  });
});
