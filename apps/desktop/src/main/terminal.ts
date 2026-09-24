import { randomUUID } from "node:crypto";
import { BrowserWindow } from "electron";
import * as pty from "node-pty";
import type { IPty } from "node-pty";
import type { TerminalSession } from "../shared/types";
import { PathSecurityError } from "../shared/security";
import { getWorkspace } from "./workspace";
import { desktopLog } from "./logger";

interface TerminalEntry {
  session: TerminalSession;
  pty: IPty;
  buffer: string;
}

const terminals = new Map<string, TerminalEntry>();
const MAX_BUFFER = 256_000;

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

function defaultShell(): string {
  if (process.platform === "win32") {
    return "powershell.exe";
  }
  return process.env.SHELL || "/bin/bash";
}

function shellTitle(shell: string): string {
  const base = shell.replace(/\\/g, "/").split("/").pop() ?? shell;
  return base.replace(/\.exe$/i, "").toLowerCase();
}

function terminalEnv(): Record<string, string> {
  return {
    ...process.env,
    TERM: "xterm-256color",
    COLORTERM: "truecolor",
    FORCE_COLOR: "1",
  } as Record<string, string>;
}

function applyShellTheme(ptyProcess: IPty): void {
  setTimeout(() => {
    if (process.platform === "win32") {
      ptyProcess.write(
        "$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()\r",
      );
      return;
    }
    ptyProcess.write(
      "export PS1='\\[\\033[1;36m\\]\\u@\\h\\[\\033[0m\\]:\\[\\033[33m\\]\\w\\[\\033[0m\\]\\[\\033[90m\\] $\\[\\033[0m\\]'\r",
    );
  }, 80);
}

export function createTerminal(cwd?: string): TerminalSession {
  const ws = getWorkspace();
  const workingDir = cwd ?? ws?.rootPath ?? process.cwd();
  const shell = defaultShell();
  const session: TerminalSession = {
    id: randomUUID(),
    cwd: workingDir,
    title: shellTitle(shell),
    state: "running",
    exitCode: null,
  };

  const shellArgs = process.platform === "win32" ? ["-NoLogo"] : [];
  const ptyProcess = pty.spawn(shell, shellArgs, {
    name: "xterm-256color",
    cols: 80,
    rows: 24,
    cwd: workingDir,
    env: terminalEnv(),
  });

  applyShellTheme(ptyProcess);

  ptyProcess.onData((data) => {
    const entry = terminals.get(session.id);
    if (entry) {
      entry.buffer += data;
      if (entry.buffer.length > MAX_BUFFER) {
        entry.buffer = entry.buffer.slice(-MAX_BUFFER);
      }
    }
    emit({ terminalId: session.id, type: "stdout", data });
  });

  ptyProcess.onExit(({ exitCode }) => {
    emit({ terminalId: session.id, type: "exit", data: "", exitCode });
    const entry = terminals.get(session.id);
    if (entry) {
      entry.session.state = "exited";
      entry.session.exitCode = exitCode;
    }
  });

  terminals.set(session.id, { session, pty: ptyProcess, buffer: "" });
  return session;
}

export function replayTerminal(terminalId: string): void {
  const entry = terminals.get(terminalId);
  if (!entry || !entry.buffer) return;
  emit({ terminalId, type: "stdout", data: entry.buffer });
}

export function writeTerminal(terminalId: string, data: string): void {
  const entry = terminals.get(terminalId);
  if (!entry) throw new PathSecurityError("Terminal not found");
  entry.pty.write(data);
}

export function resizeTerminal(terminalId: string, cols: number, rows: number): void {
  const entry = terminals.get(terminalId);
  if (!entry) throw new PathSecurityError("Terminal not found");
  if (cols > 0 && rows > 0) {
    entry.pty.resize(cols, rows);
  }
}

export function killTerminal(terminalId: string): void {
  const entry = terminals.get(terminalId);
  if (!entry) return;
  try {
    entry.pty.kill();
  } catch (err) {
    desktopLog.error("terminal", err instanceof Error ? err.message : String(err));
  }
  terminals.delete(terminalId);
}

export function clearTerminal(terminalId: string): void {
  writeTerminal(terminalId, process.platform === "win32" ? "\f" : "\x1b[2J\x1b[H");
}

export function cleanupTerminals(): void {
  for (const id of terminals.keys()) {
    killTerminal(id);
  }
}
