import { app } from "electron";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import type { DesktopSettings } from "../shared/types";

const DEFAULT_SETTINGS: DesktopSettings = {
  apiUrl: process.env.AI_PLATFORM_DESKTOP_API_URL ?? "http://127.0.0.1:8000",
  agentUrl: process.env.AI_PLATFORM_AGENT_URL ?? "http://127.0.0.1:8001",
  indexerUrl: process.env.AI_PLATFORM_INDEXER_URL ?? "http://127.0.0.1:8002",
  defaultModel: "default",
  theme: "dark",
  fontSize: 14,
  wordWrap: true,
  minimap: true,
  devtools: process.env.AI_PLATFORM_DESKTOP_DEVTOOLS === "true",
  maxAgentIterations: 25,
  evalMaxSamples: 10,
  inlineCompletionEnabled: process.env.AI_PLATFORM_COMPLETION_ENABLED !== "false",
  completionModel: process.env.AI_PLATFORM_COMPLETION_MODEL ?? "development-mock-v1",
  completionDebounceMs: Number(process.env.AI_PLATFORM_COMPLETION_DEBOUNCE_MS ?? 250),
  completionMaxTokens: Number(process.env.AI_PLATFORM_COMPLETION_MAX_OUTPUT_TOKENS ?? 256),
  completionContextLines: Number(process.env.AI_PLATFORM_COMPLETION_MAX_CONTEXT_LINES ?? 50),
  completionRepositoryContextEnabled:
    process.env.AI_PLATFORM_COMPLETION_REPOSITORY_CONTEXT !== "false",
  completionMaxRequestsPerMinute: Number(
    process.env.AI_PLATFORM_COMPLETION_MAX_REQUESTS_PER_MINUTE ?? 60,
  ),
  completionTimeoutMs: Number(process.env.AI_PLATFORM_COMPLETION_TIMEOUT_MS ?? 5000),
  completionTriggerOnTyping: true,
  autoSave: false,
};

function settingsPath(): string {
  const dir = join(app.getPath("userData"), "settings");
  mkdirSync(dir, { recursive: true });
  return join(dir, "desktop.json");
}

export function loadSettings(): DesktopSettings {
  const path = settingsPath();
  if (!existsSync(path)) {
    return { ...DEFAULT_SETTINGS };
  }
  try {
    const raw = JSON.parse(readFileSync(path, "utf-8")) as Partial<DesktopSettings>;
    return { ...DEFAULT_SETTINGS, ...raw };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

export function saveSettings(partial: Partial<DesktopSettings>): DesktopSettings {
  const current = loadSettings();
  const next = { ...current, ...partial };
  writeFileSync(settingsPath(), JSON.stringify(next, null, 2), "utf-8");
  return next;
}
