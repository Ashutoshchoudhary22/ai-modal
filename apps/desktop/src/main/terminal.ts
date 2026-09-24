import { randomUUID } from "node:crypto";
import { spawn } from "node:child_process";
import type { ChildProcess } from "node:child_process";
import { BrowserWindow } from "electron";
import type { TerminalSession } from "../shared/types";
import { validateTerminalCommand, PathSecurityError } from "../shared/security";
import { getWorkspace } from "./workspace";
import { desktopLog } from "./logger";

interface TerminalProcess {
  session: TerminalSession;
  process: ChildProcess | null;
}

const terminals = new Map<string, TerminalProcess>();
const MAX_SCROLLBACK = 5000;

function emit(event: {
  terminalId: string;
  type: "stdout" | "stderr" | "exit" | "error";
  data: string;
  exitCode?: number;
}): void {
  for (const win of BrowserWindow.getAllWindows()) {
    win.webContents.send("terminal:output", event);
  }
}

export function createTerminal(cwd?: string): TerminalSession {
  const ws = getWorkspace();
  const workingDir = cwd ?? ws?.rootPath ?? process.cwd();
  const session: TerminalSession = {
    id: randomUUID(),
    cwd: workingDir,
    state: "running",
    exitCode: null,
  };
  terminals.set(session.id, { session, process: null });
  return session;
}

export function executeTerminal(terminalId: string, command: string): void {
  const entry = terminals.get(terminalId);
  if (!entry) throw new PathSecurityError("Terminal not found");
  if (entry.process) {
    throw new PathSecurityError("Terminal already running a command");
  }

  validateTerminalCommand(command);
  const shell = process.platform === "win32" ? "cmd.exe" : "/bin/sh";
  const args =
    process.platform === "win32" ? ["/c", command] : ["-c", command];

  const child = spawn(shell, args, {
    cwd: entry.session.cwd,
    env: { ...process.env, TERM: "xterm-256color" },
    windowsHide: true,
  });

  entry.process = child;
  let scrollback = "";

  const append = (type: "stdout" | "stderr", chunk: string) => {
    scrollback += chunk;
    if (scrollback.length > MAX_SCROLLBACK) {
      scrollback = scrollback.slice(-MAX_SCROLLBACK);
    }
    emit({ terminalId, type, data: chunk });
  };

  child.stdout?.on("data", (data: Buffer) => append("stdout", data.toString()));
  child.stderr?.on("data", (data: Buffer) => append("stderr", data.toString()));

  child.on("close", (code) => {
    entry.process = null;
    entry.session.state = "exited";
    entry.session.exitCode = code ?? 0;
    emit({ terminalId, type: "exit", data: "", exitCode: code ?? 0 });
    entry.session.state = "running";
    entry.session.exitCode = null;
  });

  child.on("error", (err) => {
    entry.process = null;
    emit({ terminalId, type: "error", data: err.message });
    desktopLog.error("terminal", err.message);
  });
}

export function killTerminal(terminalId: string): void {
  const entry = terminals.get(terminalId);
  if (!entry) return;
  entry.process?.kill();
  entry.process = null;
}

export function clearTerminal(terminalId: string): void {
  emit({ terminalId, type: "stdout", data: "\x1b[2J\x1b[H" });
}

export function cleanupTerminals(): void {
  for (const [id, entry] of terminals) {
    entry.process?.kill();
    terminals.delete(id);
  }
}
