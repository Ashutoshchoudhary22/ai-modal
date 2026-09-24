import { contextBridge, ipcRenderer } from "electron";
import type {
  DesktopAPI,
  DesktopSettings,
  FileEntry,
  FileReadResult,
  FileWriteResult,
  GitDiffResult,
  GitStatusResult,
  OpenDialogResult,
  OpenFileDialogResult,
  SaveFileDialogResult,
  ProjectInfo,
  RecentWorkspace,
  TerminalOutputEvent,
  TerminalSession,
  WorkspaceState,
  DesktopError,
} from "../shared/types";

function isError(value: unknown): value is DesktopError {
  return (
    typeof value === "object" &&
    value !== null &&
    "code" in value &&
    "message" in value &&
    !("rootPath" in value)
  );
}

const desktopAPI: DesktopAPI = {
  workspace: {
    open: () => ipcRenderer.invoke("workspace:open"),
    openPath: (rootPath: string) => ipcRenderer.invoke("workspace:openPath", rootPath),
    close: () => ipcRenderer.invoke("workspace:close"),
    get: () => ipcRenderer.invoke("workspace:get"),
    getProjectInfo: () => ipcRenderer.invoke("workspace:projectInfo"),
    getRecents: () => ipcRenderer.invoke("workspace:recents"),
    removeRecent: (rootPath: string) => ipcRenderer.invoke("workspace:removeRecent", rootPath),
  },
  files: {
    list: (relativePath?: string) => ipcRenderer.invoke("files:list", relativePath),
    read: (relativePath: string) => ipcRenderer.invoke("files:read", relativePath),
    write: (relativePath: string, content: string) =>
      ipcRenderer.invoke("files:write", relativePath, content),
    create: (relativePath: string, type: "file" | "directory") =>
      ipcRenderer.invoke("files:create", relativePath, type),
    rename: (fromPath: string, toPath: string) =>
      ipcRenderer.invoke("files:rename", fromPath, toPath),
    delete: (relativePath: string) => ipcRenderer.invoke("files:delete", relativePath),
    search: (query: string) => ipcRenderer.invoke("files:search", query),
    onChanged: (callback) => {
      const handler = (_event: Electron.IpcRendererEvent, data: { path: string; type: string }) =>
        callback(data);
      ipcRenderer.on("files:changed", handler);
      return () => ipcRenderer.removeListener("files:changed", handler);
    },
  },
  terminal: {
    create: (cwd?: string) => ipcRenderer.invoke("terminal:create", cwd),
    write: (terminalId: string, data: string) =>
      ipcRenderer.invoke("terminal:write", terminalId, data),
    resize: (terminalId: string, cols: number, rows: number) =>
      ipcRenderer.invoke("terminal:resize", terminalId, cols, rows),
    kill: (terminalId: string) => ipcRenderer.invoke("terminal:kill", terminalId),
    clear: (terminalId: string) => ipcRenderer.invoke("terminal:clear", terminalId),
    replay: (terminalId: string) => ipcRenderer.invoke("terminal:replay", terminalId),
    onOutput: (callback) => {
      const handler = (_event: Electron.IpcRendererEvent, data: TerminalOutputEvent) =>
        callback(data);
      ipcRenderer.on("terminal:output", handler);
      return () => ipcRenderer.removeListener("terminal:output", handler);
    },
  },
  git: {
    status: () => ipcRenderer.invoke("git:status"),
    diff: (path?: string) => ipcRenderer.invoke("git:diff", path),
    log: (limit?: number) => ipcRenderer.invoke("git:log", limit),
  },
  settings: {
    get: () => ipcRenderer.invoke("settings:get"),
    set: (partial: Partial<DesktopSettings>) => ipcRenderer.invoke("settings:set", partial),
  },
  window: {
    openExternal: (url: string) => ipcRenderer.invoke("window:openExternal", url),
    showOpenDialog: () => ipcRenderer.invoke("window:showOpenDialog"),
    openFileDialog: () => ipcRenderer.invoke("window:openFileDialog"),
    saveFileDialog: (defaultPath?: string) => ipcRenderer.invoke("window:saveFileDialog", defaultPath),
    openWorkspaceFileDialog: () => ipcRenderer.invoke("window:openWorkspaceFileDialog"),
    newWindow: () => ipcRenderer.invoke("window:newWindow"),
    closeWindow: () => ipcRenderer.invoke("window:closeWindow"),
    quit: () => ipcRenderer.invoke("window:quit"),
  },
  platform: {
    isMac: process.platform === "darwin",
    isWindows: process.platform === "win32",
    isLinux: process.platform === "linux",
  },
};

contextBridge.exposeInMainWorld("desktop", desktopAPI);

export type { DesktopAPI, DesktopError, WorkspaceState };
export { isError };
