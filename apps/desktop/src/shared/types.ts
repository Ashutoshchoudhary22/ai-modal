/** Shared types for desktop preload bridge and renderer. */

export interface DesktopError {
  code: string;
  message: string;
}

export interface WorkspaceState {
  workspaceId: string;
  rootPath: string;
  name: string;
  openedAt: string;
  indexStatus: "idle" | "indexing" | "indexed" | "failed";
  indexerWorkspaceId: string | null;
  gitBranch: string | null;
}

export interface FileEntry {
  name: string;
  path: string;
  type: "file" | "directory";
  children?: FileEntry[];
}

export interface FileReadResult {
  path: string;
  content: string;
  encoding: "utf-8";
}

export interface FileWriteResult {
  path: string;
  success: boolean;
}

export interface TerminalSession {
  id: string;
  cwd: string;
  state: "running" | "exited";
  exitCode: number | null;
}

export interface TerminalOutputEvent {
  terminalId: string;
  type: "stdout" | "stderr" | "exit" | "error";
  data: string;
  exitCode?: number;
}

export interface GitStatusResult {
  branch: string | null;
  modified: string[];
  added: string[];
  deleted: string[];
  untracked: string[];
}

export interface GitDiffResult {
  path: string;
  diff: string;
}

export interface DesktopSettings {
  apiUrl: string;
  agentUrl: string;
  indexerUrl: string;
  defaultModel: string;
  theme: "dark" | "light" | "system";
  fontSize: number;
  wordWrap: boolean;
  minimap: boolean;
  devtools: boolean;
  maxAgentIterations: number;
  evalMaxSamples: number;
  inlineCompletionEnabled: boolean;
  completionModel: string;
  completionDebounceMs: number;
  completionMaxTokens: number;
  completionContextLines: number;
  completionRepositoryContextEnabled: boolean;
  completionMaxRequestsPerMinute: number;
  completionTimeoutMs: number;
  completionTriggerOnTyping: boolean;
}

export interface RecentWorkspace {
  rootPath: string;
  name: string;
  openedAt: string;
}

export interface OpenDialogResult {
  canceled: boolean;
  path: string | null;
}

export interface ProjectInfo {
  type: "node" | "python" | "php" | "java" | "unknown";
  scripts: string[];
}

export type ApiHealthStatus = "connected" | "disconnected" | "connecting" | "error";

export interface DesktopAPI {
  workspace: {
    open: () => Promise<WorkspaceState | DesktopError>;
    openPath: (rootPath: string) => Promise<WorkspaceState | DesktopError>;
    close: () => Promise<void>;
    get: () => Promise<WorkspaceState | null>;
    getProjectInfo: () => Promise<ProjectInfo | null>;
    getRecents: () => Promise<RecentWorkspace[]>;
    removeRecent: (rootPath: string) => Promise<void>;
  };
  files: {
    list: (relativePath?: string) => Promise<FileEntry[] | DesktopError>;
    read: (relativePath: string) => Promise<FileReadResult | DesktopError>;
    write: (relativePath: string, content: string) => Promise<FileWriteResult | DesktopError>;
    create: (relativePath: string, type: "file" | "directory") => Promise<void | DesktopError>;
    rename: (fromPath: string, toPath: string) => Promise<void | DesktopError>;
    delete: (relativePath: string) => Promise<void | DesktopError>;
    search: (query: string) => Promise<string[] | DesktopError>;
    onChanged: (callback: (event: { path: string; type: string }) => void) => () => void;
  };
  terminal: {
    create: (cwd?: string) => Promise<TerminalSession | DesktopError>;
    execute: (terminalId: string, command: string) => Promise<void | DesktopError>;
    kill: (terminalId: string) => Promise<void>;
    clear: (terminalId: string) => Promise<void>;
    onOutput: (callback: (event: TerminalOutputEvent) => void) => () => void;
  };
  git: {
    status: () => Promise<GitStatusResult | DesktopError>;
    diff: (path?: string) => Promise<GitDiffResult | DesktopError>;
    log: (limit?: number) => Promise<string | DesktopError>;
  };
  settings: {
    get: () => Promise<DesktopSettings>;
    set: (partial: Partial<DesktopSettings>) => Promise<DesktopSettings>;
  };
  window: {
    openExternal: (url: string) => Promise<void>;
    showOpenDialog: () => Promise<OpenDialogResult>;
  };
  platform: {
    isMac: boolean;
    isWindows: boolean;
    isLinux: boolean;
  };
}

declare global {
  interface Window {
    desktop: DesktopAPI;
  }
}
