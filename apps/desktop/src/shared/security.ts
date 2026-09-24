/** Workspace path security — mirrors Phase 5 / code-indexer rules. */

import { basename, resolve, relative, isAbsolute } from "node:path";

export const SENSITIVE_PATTERNS = [
  ".env",
  ".pem",
  ".key",
  "credentials.",
  "secrets.",
];

export class PathSecurityError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PathSecurityError";
  }
}

export function resolveWorkspacePath(workspaceRoot: string): string {
  const root = resolve(workspaceRoot);
  return root;
}

export function resolveRelativePath(workspaceRoot: string, relativePath: string): string {
  const root = resolve(workspaceRoot);
  const normalized = relativePath.replace(/\\/g, "/").replace(/^\/+/, "");
  if (normalized.split("/").some((part) => part === "..")) {
    throw new PathSecurityError(`Path traversal rejected: ${relativePath}`);
  }
  const candidate = resolve(root, normalized);
  const rel = relative(root, candidate);
  if (rel.startsWith("..") || isAbsolute(rel)) {
    throw new PathSecurityError(`Path escapes workspace: ${relativePath}`);
  }
  return candidate;
}

export function assertNotSensitive(relativePath: string, write = false): void {
  const normalized = relativePath.replace(/\\/g, "/");
  const base = basename(normalized);
  if (normalized.endsWith(".env.example")) {
    return;
  }
  for (const pattern of SENSITIVE_PATTERNS) {
    if (pattern.endsWith(".")) {
      if (base.startsWith(pattern)) {
        throw new PathSecurityError(`Access to sensitive file denied: ${relativePath}`);
      }
    } else if (
      base === pattern ||
      normalized.includes(`/${pattern}`) ||
      base.endsWith(pattern)
    ) {
      throw new PathSecurityError(`Access to sensitive file denied: ${relativePath}`);
    }
  }
  if (write && base === ".env") {
    throw new PathSecurityError(`Writing sensitive file denied: ${relativePath}`);
  }
}

export function isSensitivePath(relativePath: string): boolean {
  try {
    assertNotSensitive(relativePath);
    return false;
  } catch {
    return true;
  }
}

const DENIED_COMMANDS = ["rm -rf", "del /f", "format ", "mkfs", "shutdown", "reboot"];
const DENIED_METACHAR = [";", "|", "&&", "||", ">", "<", "`", "$(", "${"];

export function validateTerminalCommand(command: string): void {
  const trimmed = command.trim();
  if (!trimmed) {
    throw new PathSecurityError("Empty command");
  }
  for (const token of DENIED_METACHAR) {
    if (command.includes(token)) {
      throw new PathSecurityError(`Shell metacharacters are not allowed: ${token}`);
    }
  }
  const lower = trimmed.toLowerCase();
  for (const denied of DENIED_COMMANDS) {
    if (lower.includes(denied)) {
      throw new PathSecurityError(`Command not allowed: ${denied}`);
    }
  }
}
