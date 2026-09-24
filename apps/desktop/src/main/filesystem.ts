import {
  readdirSync,
  readFileSync,
  writeFileSync,
  mkdirSync,
  renameSync,
  unlinkSync,
  rmdirSync,
  statSync,
  existsSync,
  watch,
} from "node:fs";
import { isAbsolute, join, relative } from "node:path";
import type { FSWatcher } from "node:fs";
import { BrowserWindow } from "electron";
import type { FileEntry } from "../shared/types";
import {
  assertNotSensitive,
  resolveRelativePath,
  PathSecurityError,
} from "../shared/security";
import { getWorkspace } from "./workspace";
import { desktopLog } from "./logger";

const IGNORED = new Set([
  "node_modules",
  ".git",
  ".venv",
  "venv",
  "__pycache__",
  ".pytest_cache",
  "dist",
  "build",
  ".next",
  "out",
  "release",
]);

let watcher: FSWatcher | null = null;

export function startFileWatcher(): void {
  stopFileWatcher();
  const ws = getWorkspace();
  if (!ws) return;
  try {
    watcher = watch(ws.rootPath, { recursive: true }, (_event, filename) => {
      if (!filename) return;
      const windows = BrowserWindow.getAllWindows();
      for (const win of windows) {
        win.webContents.send("files:changed", {
          path: filename.replace(/\\/g, "/"),
          type: _event,
        });
      }
    });
  } catch (err) {
    desktopLog.warn("filesystem", `Watcher failed: ${String(err)}`);
  }
}

export function stopFileWatcher(): void {
  watcher?.close();
  watcher = null;
}

function requireWorkspace(): string {
  const ws = getWorkspace();
  if (!ws) throw new PathSecurityError("No workspace open");
  return ws.rootPath;
}

export function listFiles(relativePath = ""): FileEntry[] {
  const root = requireWorkspace();
  const dirPath = resolveRelativePath(root, relativePath || ".");
  if (!statSync(dirPath).isDirectory()) {
    throw new PathSecurityError("Not a directory");
  }
  const entries = readdirSync(dirPath, { withFileTypes: true });
  const result: FileEntry[] = [];
  for (const entry of entries) {
    if (IGNORED.has(entry.name)) continue;
    const rel = relative(root, join(dirPath, entry.name)).replace(/\\/g, "/");
    if (entry.isDirectory()) {
      result.push({ name: entry.name, path: rel, type: "directory" });
    } else {
      result.push({ name: entry.name, path: rel, type: "file" });
    }
  }
  return result.sort((a, b) => {
    if (a.type !== b.type) return a.type === "directory" ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
}

function resolveFilePath(filePath: string): string {
  if (isAbsolute(filePath)) return filePath;
  const root = requireWorkspace();
  assertNotSensitive(filePath);
  return resolveRelativePath(root, filePath);
}

export function readFile(filePath: string): { path: string; content: string } {
  const abs = resolveFilePath(filePath);
  const content = readFileSync(abs, "utf-8");
  const ws = getWorkspace();
  const path =
    ws && !isAbsolute(filePath)
      ? filePath
      : abs.replace(/\\/g, "/");
  return { path, content, encoding: "utf-8" as const };
}

export function writeFile(filePath: string, content: string): { path: string; success: boolean } {
  const abs = resolveFilePath(filePath);
  if (!isAbsolute(filePath)) {
    assertNotSensitive(filePath, true);
  }
  const dir = join(abs, "..");
  mkdirSync(dir, { recursive: true });
  writeFileSync(abs, content, "utf-8");
  const ws = getWorkspace();
  const path =
    ws && !isAbsolute(filePath)
      ? filePath
      : abs.replace(/\\/g, "/");
  return { path, success: true };
}

export function createEntry(relativePath: string, type: "file" | "directory"): void {
  const root = requireWorkspace();
  assertNotSensitive(relativePath, true);
  const abs = resolveRelativePath(root, relativePath);
  if (type === "directory") {
    mkdirSync(abs, { recursive: true });
  } else {
    mkdirSync(join(abs, ".."), { recursive: true });
    if (!existsSync(abs)) writeFileSync(abs, "", "utf-8");
  }
}

export function renameEntry(fromPath: string, toPath: string): void {
  const root = requireWorkspace();
  assertNotSensitive(fromPath, true);
  assertNotSensitive(toPath, true);
  const fromAbs = resolveRelativePath(root, fromPath);
  const toAbs = resolveRelativePath(root, toPath);
  renameSync(fromAbs, toAbs);
}

export function deleteEntry(relativePath: string): void {
  const root = requireWorkspace();
  assertNotSensitive(relativePath, true);
  const abs = resolveRelativePath(root, relativePath);
  const stat = statSync(abs);
  if (stat.isDirectory()) {
    rmdirSync(abs, { recursive: true });
  } else {
    unlinkSync(abs);
  }
}

export function searchFiles(query: string): string[] {
  const root = requireWorkspace();
  const results: string[] = [];
  const lower = query.toLowerCase();

  function walk(dir: string): void {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      if (IGNORED.has(entry.name)) continue;
      const abs = join(dir, entry.name);
      const rel = relative(root, abs).replace(/\\/g, "/");
      if (entry.isDirectory()) {
        walk(abs);
      } else {
        try {
          assertNotSensitive(rel);
          const content = readFileSync(abs, "utf-8");
          if (content.toLowerCase().includes(lower) || rel.toLowerCase().includes(lower)) {
            results.push(rel);
          }
        } catch {
          /* skip binary / sensitive */
        }
      }
      if (results.length >= 100) return;
    }
  }

  walk(root);
  return results;
}
