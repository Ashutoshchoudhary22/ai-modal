import { randomUUID } from "node:crypto";
import { basename, join } from "node:path";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { app } from "electron";
import type { ProjectInfo, RecentWorkspace, WorkspaceState } from "../shared/types";
import { resolveWorkspacePath } from "../shared/security";
import { desktopLog } from "./logger";

let currentWorkspace: WorkspaceState | null = null;

function recentsPath(): string {
  const dir = join(app.getPath("userData"), "settings");
  mkdirSync(dir, { recursive: true });
  return join(dir, "recent-workspaces.json");
}

export function getWorkspace(): WorkspaceState | null {
  return currentWorkspace;
}

export function openWorkspace(rootPath: string): WorkspaceState {
  const resolved = resolveWorkspacePath(rootPath);
  if (!existsSync(resolved)) {
    throw new Error(`Workspace does not exist: ${resolved}`);
  }
  currentWorkspace = {
    workspaceId: randomUUID(),
    rootPath: resolved,
    name: basename(resolved),
    openedAt: new Date().toISOString(),
    indexStatus: "idle",
    indexerWorkspaceId: null,
    gitBranch: null,
  };
  addRecent(resolved);
  desktopLog.info("workspace", `Opened workspace: ${resolved}`);
  return currentWorkspace;
}

export function closeWorkspace(): void {
  currentWorkspace = null;
  desktopLog.info("workspace", "Workspace closed");
}

export function setIndexStatus(
  status: WorkspaceState["indexStatus"],
  indexerWorkspaceId?: string | null,
): void {
  if (!currentWorkspace) return;
  currentWorkspace = {
    ...currentWorkspace,
    indexStatus: status,
    indexerWorkspaceId: indexerWorkspaceId ?? currentWorkspace.indexerWorkspaceId,
  };
}

export function setGitBranch(branch: string | null): void {
  if (!currentWorkspace) return;
  currentWorkspace = { ...currentWorkspace, gitBranch: branch };
}

function addRecent(rootPath: string): void {
  const recents = getRecents().filter((r) => r.rootPath !== rootPath);
  recents.unshift({
    rootPath,
    name: basename(rootPath),
    openedAt: new Date().toISOString(),
  });
  writeFileSync(recentsPath(), JSON.stringify(recents.slice(0, 10), null, 2));
}

export function getRecents(): RecentWorkspace[] {
  const path = recentsPath();
  if (!existsSync(path)) return [];
  try {
    return JSON.parse(readFileSync(path, "utf-8")) as RecentWorkspace[];
  } catch {
    return [];
  }
}

export function removeRecent(rootPath: string): void {
  const recents = getRecents().filter((r) => r.rootPath !== rootPath);
  writeFileSync(recentsPath(), JSON.stringify(recents, null, 2));
}

export function detectProjectInfo(): ProjectInfo | null {
  if (!currentWorkspace) return null;
  const root = currentWorkspace.rootPath;
  const scripts: string[] = [];
  let type: ProjectInfo["type"] = "unknown";

  if (existsSync(join(root, "package.json"))) {
    type = "node";
    try {
      const pkg = JSON.parse(readFileSync(join(root, "package.json"), "utf-8")) as {
        scripts?: Record<string, string>;
      };
      for (const [name] of Object.entries(pkg.scripts ?? {})) {
        scripts.push(`npm run ${name}`);
      }
    } catch {
      /* ignore */
    }
  } else if (existsSync(join(root, "pyproject.toml")) || existsSync(join(root, "requirements.txt"))) {
    type = "python";
    scripts.push("pytest");
  } else if (existsSync(join(root, "composer.json"))) {
    type = "php";
  } else if (existsSync(join(root, "pom.xml")) || existsSync(join(root, "build.gradle"))) {
    type = "java";
  }

  return { type, scripts };
}
