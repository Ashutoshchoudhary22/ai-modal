import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { GitDiffResult, GitStatusResult } from "../shared/types";
import { getWorkspace } from "./workspace";
import { PathSecurityError } from "../shared/security";

const execFileAsync = promisify(execFile);

function requireWorkspace(): string {
  const ws = getWorkspace();
  if (!ws) throw new PathSecurityError("No workspace open");
  return ws.rootPath;
}

async function git(args: string[]): Promise<string> {
  const cwd = requireWorkspace();
  const { stdout } = await execFileAsync("git", args, {
    cwd,
    maxBuffer: 2 * 1024 * 1024,
    windowsHide: true,
  });
  return stdout;
}

export async function gitStatus(): Promise<GitStatusResult> {
  const result: GitStatusResult = {
    branch: null,
    modified: [],
    added: [],
    deleted: [],
    untracked: [],
  };
  try {
    result.branch = (await git(["rev-parse", "--abbrev-ref", "HEAD"])).trim();
  } catch {
    return result;
  }

  const status = await git(["status", "--porcelain"]);
  for (const line of status.split("\n").filter(Boolean)) {
    const code = line.slice(0, 2);
    const file = line.slice(3).trim();
    if (code === "??") result.untracked.push(file);
    else if (code.includes("A")) result.added.push(file);
    else if (code.includes("D")) result.deleted.push(file);
    else if (code.includes("M")) result.modified.push(file);
  }
  return result;
}

export async function gitDiff(path?: string): Promise<GitDiffResult> {
  const args = ["diff", "--"];
  if (path) args.push(path);
  const diff = await git(args);
  return { path: path ?? ".", diff };
}

export async function gitLog(limit = 20): Promise<string> {
  return git(["log", `--oneline`, `-n`, String(limit)]);
}
