import { describe, expect, it } from "vitest";
import {
  calculatePrefix,
  calculateSuffix,
  deduplicateCompletion,
  extractImports,
  extractNearbyCode,
  isCompletionAllowed,
  shouldTriggerCompletion,
} from "../src/renderer/src/features/completion/completionUtils";

describe("completionUtils", () => {
  it("calculates prefix and suffix", () => {
    const content = "hello world";
    expect(calculatePrefix(content, 5)).toBe("hello");
    expect(calculateSuffix(content, 5)).toBe(" world");
  });

  it("extracts nearby code", () => {
    const content = "line1\nline2\nline3\nline4";
    const nearby = extractNearbyCode(content, 2, 1);
    expect(nearby).toContain("line2");
    expect(nearby).toContain("line3");
  });

  it("extracts imports", () => {
    const content = "import x from 'y';\nconst a = 1;";
    expect(extractImports(content)).toHaveLength(1);
  });

  it("blocks sensitive files", () => {
    expect(isCompletionAllowed(".env", true)).toBe(false);
    expect(isCompletionAllowed("src/main.ts", true)).toBe(true);
    expect(isCompletionAllowed("src/main.ts", false)).toBe(false);
  });

  it("deduplicates prefix overlap", () => {
    expect(deduplicateCompletion("prefixtext", "prefix", "")).toBe("text");
  });

  it("detects trigger characters", () => {
    expect(shouldTriggerCompletion(".", true)).toBe(true);
    expect(shouldTriggerCompletion("a", true)).toBe(true);
    expect(shouldTriggerCompletion(".", false)).toBe(false);
  });
});
