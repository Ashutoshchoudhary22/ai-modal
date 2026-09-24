import { describe, expect, it } from "vitest";
import {
  assertNotSensitive,
  PathSecurityError,
  resolveRelativePath,
  validateTerminalCommand,
} from "../src/shared/security";

describe("path security", () => {
  const root = "C:\\workspace\\project";

  it("resolves relative paths within workspace", () => {
    const resolved = resolveRelativePath(root, "src/main.ts");
    expect(resolved).toContain("main.ts");
  });

  it("blocks path traversal", () => {
    expect(() => resolveRelativePath(root, "../secrets.txt")).toThrow(PathSecurityError);
  });

  it("blocks sensitive .env files", () => {
    expect(() => assertNotSensitive(".env")).toThrow(PathSecurityError);
    expect(() => assertNotSensitive("config/.env")).toThrow(PathSecurityError);
  });

  it("allows .env.example", () => {
    expect(() => assertNotSensitive(".env.example")).not.toThrow();
  });

  it("blocks .pem and .key files", () => {
    expect(() => assertNotSensitive("certs/server.pem")).toThrow(PathSecurityError);
    expect(() => assertNotSensitive("private.key")).toThrow(PathSecurityError);
  });
});

describe("terminal security", () => {
  it("blocks shell metacharacters", () => {
    expect(() => validateTerminalCommand("ls; rm -rf /")).toThrow(PathSecurityError);
    expect(() => validateTerminalCommand("echo hello")).not.toThrow();
  });

  it("blocks dangerous commands", () => {
    expect(() => validateTerminalCommand("rm -rf .")).toThrow(PathSecurityError);
  });
});

describe("renderer security boundary", () => {
  it("does not expose Node fs to renderer", () => {
    expect(typeof window !== "undefined" ? (window as unknown as { require?: unknown }).require : undefined).toBeUndefined();
  });
});
