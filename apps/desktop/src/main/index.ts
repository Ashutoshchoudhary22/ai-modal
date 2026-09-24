import { app, BrowserWindow, ipcMain, dialog, shell } from "electron";
import { join } from "node:path";
import { PathSecurityError } from "../shared/security";
import type { DesktopError, DesktopSettings } from "../shared/types";
import { desktopLog } from "./logger";
import { loadSettings, saveSettings } from "./settings";
import {
  openWorkspace,
  closeWorkspace,
  getWorkspace,
  getRecents,
  removeRecent,
  detectProjectInfo,
  setIndexStatus,
  setGitBranch,
} from "./workspace";
import {
  listFiles,
  readFile,
  writeFile,
  createEntry,
  renameEntry,
  deleteEntry,
  searchFiles,
  startFileWatcher,
  stopFileWatcher,
} from "./filesystem";
import {
  createTerminal,
  executeTerminal,
  killTerminal,
  clearTerminal,
  cleanupTerminals,
} from "./terminal";
import { gitStatus, gitDiff, gitLog } from "./git";

let mainWindow: BrowserWindow | null = null;

function toError(err: unknown): DesktopError {
  if (err instanceof PathSecurityError) {
    return { code: "PATH_SECURITY", message: err.message };
  }
  if (err instanceof Error) {
    return { code: "ERROR", message: err.message };
  }
  return { code: "ERROR", message: String(err) };
}

async function triggerIndexing(): Promise<void> {
  const ws = getWorkspace();
  if (!ws) return;
  const settings = loadSettings();
  setIndexStatus("indexing");
  try {
    const createRes = await fetch(`${settings.indexerUrl}/v1/workspaces`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: ws.name, root_path: ws.rootPath }),
    });
    if (!createRes.ok) throw new Error(`Indexer create failed: ${createRes.status}`);
    const created = (await createRes.json()) as { id: string };
    const indexRes = await fetch(
      `${settings.indexerUrl}/v1/workspaces/${created.id}/index`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ root_path: ws.rootPath }),
      },
    );
    if (!indexRes.ok) throw new Error(`Indexer index failed: ${indexRes.status}`);
    setIndexStatus("indexed", created.id);
  } catch (err) {
    setIndexStatus("failed");
    desktopLog.warn("indexer", String(err));
  }
}

async function updateGitBranch(): Promise<void> {
  try {
    const status = await gitStatus();
    setGitBranch(status.branch);
  } catch {
    setGitBranch(null);
  }
}

function createWindow(): void {
  const settings = loadSettings();
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 720,
    title: "AI Platform IDE",
    webPreferences: {
      preload: join(__dirname, "../preload/index.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL);
  } else {
    mainWindow.loadFile(join(__dirname, "../renderer/index.html"));
  }

  if (settings.devtools) {
    mainWindow.webContents.openDevTools({ mode: "detach" });
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function registerIpc(): void {
  ipcMain.handle("workspace:open", async () => {
    const result = await dialog.showOpenDialog(mainWindow!, {
      properties: ["openDirectory"],
    });
    if (result.canceled || !result.filePaths[0]) {
      return { code: "CANCELLED", message: "Cancelled" } satisfies DesktopError;
    }
    try {
      const ws = openWorkspace(result.filePaths[0]);
      startFileWatcher();
      void triggerIndexing();
      void updateGitBranch();
      return ws;
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("workspace:openPath", async (_e, rootPath: string) => {
    try {
      const ws = openWorkspace(rootPath);
      startFileWatcher();
      void triggerIndexing();
      void updateGitBranch();
      return ws;
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("workspace:close", () => {
    stopFileWatcher();
    cleanupTerminals();
    closeWorkspace();
  });

  ipcMain.handle("workspace:get", () => getWorkspace());
  ipcMain.handle("workspace:recents", () => getRecents());
  ipcMain.handle("workspace:removeRecent", (_e, rootPath: string) => removeRecent(rootPath));
  ipcMain.handle("workspace:projectInfo", () => detectProjectInfo());

  ipcMain.handle("files:list", (_e, relativePath?: string) => {
    try {
      return listFiles(relativePath);
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("files:read", (_e, relativePath: string) => {
    try {
      return readFile(relativePath);
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("files:write", (_e, relativePath: string, content: string) => {
    try {
      return writeFile(relativePath, content);
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("files:create", (_e, relativePath: string, type: "file" | "directory") => {
    try {
      createEntry(relativePath, type);
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("files:rename", (_e, fromPath: string, toPath: string) => {
    try {
      renameEntry(fromPath, toPath);
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("files:delete", (_e, relativePath: string) => {
    try {
      deleteEntry(relativePath);
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("files:search", (_e, query: string) => {
    try {
      return searchFiles(query);
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("terminal:create", (_e, cwd?: string) => {
    try {
      return createTerminal(cwd);
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("terminal:execute", (_e, terminalId: string, command: string) => {
    try {
      executeTerminal(terminalId, command);
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("terminal:kill", (_e, terminalId: string) => killTerminal(terminalId));
  ipcMain.handle("terminal:clear", (_e, terminalId: string) => clearTerminal(terminalId));

  ipcMain.handle("git:status", async () => {
    try {
      return await gitStatus();
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("git:diff", async (_e, path?: string) => {
    try {
      return await gitDiff(path);
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("git:log", async (_e, limit?: number) => {
    try {
      return await gitLog(limit);
    } catch (err) {
      return toError(err);
    }
  });

  ipcMain.handle("settings:get", () => loadSettings());
  ipcMain.handle("settings:set", (_e, partial: Partial<DesktopSettings>) =>
    saveSettings(partial),
  );

  ipcMain.handle("window:openExternal", (_e, url: string) => {
    if (url.startsWith("http://") || url.startsWith("https://")) {
      return shell.openExternal(url);
    }
  });

  ipcMain.handle("window:showOpenDialog", async () => {
    const result = await dialog.showOpenDialog(mainWindow!, {
      properties: ["openDirectory"],
    });
    return {
      canceled: result.canceled,
      path: result.filePaths[0] ?? null,
    };
  });
}

app.whenReady().then(() => {
  registerIpc();
  createWindow();
  desktopLog.info("desktop", "Application started");

  const e2eWorkspace = process.env.AI_PLATFORM_E2E_WORKSPACE;
  if (e2eWorkspace) {
    try {
      openWorkspace(e2eWorkspace);
      startFileWatcher();
      desktopLog.info("desktop", `E2E workspace opened: ${e2eWorkspace}`);
    } catch (err) {
      desktopLog.warn("desktop", `E2E workspace open failed: ${String(err)}`);
    }
  }

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  stopFileWatcher();
  cleanupTerminals();
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  stopFileWatcher();
  cleanupTerminals();
});
