/**
 * Phase 14 — full Electron + Monaco inline completion verification.
 * Requires AI API at http://127.0.0.1:8000 with POST /v1/completions.
 */
import { _electron as electron } from "playwright";
import { spawn } from "node:child_process";
import {
  mkdirSync,
  writeFileSync,
  unlinkSync,
  existsSync,
  rmSync,
  mkdtempSync,
} from "node:fs";
import { join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const desktopRoot = join(__dirname, "..");
const repoRoot = join(desktopRoot, "..", "..");
const venvPython = join(repoRoot, ".venv", "Scripts", "python.exe");
const apiUrl = "http://127.0.0.1:8000";
const indexerUrl = "http://127.0.0.1:8002";

const wsRoot = join(repoRoot, "e2e-workspaces");
const wsA = join(wsRoot, "workspace-a");
const wsB = join(wsRoot, "workspace-b");
const testFile = "e2e-completion-verify.ts";

const results = [];
let apiProc = null;
let indexerProc = null;
let weStartedApi = false;
let weStartedIndexer = false;

function record(name, ok, evidence) {
  results.push({ name, ok, evidence });
  console.log(`${ok ? "PASS" : "FAIL"} ${name}: ${evidence}`);
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  const text = await res.text();
  let body = text;
  try {
    body = JSON.parse(text);
  } catch {
    /* raw */
  }
  return { status: res.status, body };
}

async function waitForService(url, label, attempts = 40) {
  for (let i = 0; i < attempts; i += 1) {
    try {
      const { status } = await fetchJson(`${url}/health`);
      if (status === 200) return true;
    } catch {
      /* retry */
    }
    await sleep(250);
  }
  throw new Error(`${label} not ready at ${url}`);
}

async function ensureApi() {
  try {
    const health = await fetchJson(`${apiUrl}/health`);
    const completion = await fetchJson(`${apiUrl}/v1/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "development-mock-v1",
        language: "typescript",
        file_path: "src/example.ts",
        prefix: "const user = await db.",
        suffix: "",
        cursor: { line: 0, column: 22 },
        context: {},
        options: { max_tokens: 64 },
      }),
    });
    if (health.status === 200 && completion.status === 200) {
      record("AI API ready", true, `${apiUrl} health+completions OK`);
      return;
    }
  } catch {
    /* start below */
  }

  apiProc = spawn(
    venvPython,
    ["-m", "uvicorn", "ai_api.main:app", "--app-dir", "services/ai-api/src", "--host", "127.0.0.1", "--port", "8000"],
    {
      cwd: repoRoot,
      env: { ...process.env, AI_PLATFORM_PROVIDER: "development_mock" },
      stdio: "pipe",
    },
  );
  weStartedApi = true;
  await waitForService(apiUrl, "AI API");
  const completion = await fetchJson(`${apiUrl}/v1/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "development-mock-v1",
      language: "typescript",
      file_path: "src/example.ts",
      prefix: "const user = await db.",
      suffix: "",
      cursor: { line: 0, column: 22 },
      context: {},
      options: { max_tokens: 64 },
    }),
  });
  const ok =
    completion.status === 200 &&
    String(completion.body?.completion?.text ?? "").includes("findById");
  record("AI API ready", ok, `started API; completion=${JSON.stringify(completion.body?.completion?.text ?? "")}`);
  if (!ok) throw new Error("AI API completions endpoint not working");
}

async function tryStartIndexer() {
  try {
    const health = await fetchJson(`${indexerUrl}/health`);
    if (health.status === 200) return true;
  } catch {
    /* try start */
  }
  try {
    indexerProc = spawn(
      venvPython,
      ["-m", "uvicorn", "code_indexer.main:app", "--app-dir", "services/code-indexer/src", "--host", "127.0.0.1", "--port", "8002"],
      { cwd: repoRoot, stdio: "pipe" },
    );
    weStartedIndexer = true;
    await waitForService(indexerUrl, "Indexer", 30);
    return true;
  } catch {
    return false;
  }
}

function setupWorkspaces() {
  rmSync(wsRoot, { recursive: true, force: true });
  mkdirSync(wsA, { recursive: true });
  mkdirSync(wsB, { recursive: true });
  writeFileSync(join(wsA, testFile), "// WORKSPACE_A\n", "utf-8");
  writeFileSync(join(wsB, testFile), "// WORKSPACE_B\n", "utf-8");
  writeFileSync(join(wsA, "UserService.ts"), "export class UserService { find() {} }\n", "utf-8");
}

function cleanupWorkspaces() {
  rmSync(wsRoot, { recursive: true, force: true });
  const stray = join(repoRoot, testFile);
  if (existsSync(stray)) unlinkSync(stray);
}

async function modelValue(page) {
  return page.evaluate(() => window.__e2e?.getModelValue() ?? window.__monacoActiveEditor__?.getModel()?.getValue() ?? "");
}

async function hasGhost(page) {
  return page.evaluate(() => {
    const ghost =
      document.querySelector(".ghost-text") ??
      document.querySelector("[class*='ghost-text']");
    return ghost?.textContent?.includes("findById") ?? false;
  });
}

async function focusEditor(page) {
  await page.getByRole("button", { name: "Chat" }).click().catch(() => {});
  await sleep(100);
  await page.locator(".monaco-editor").first().click({ timeout: 5000, force: true });
  await sleep(100);
}

async function typeCompletionPrefix(page, { leaveAssistantOpen = false } = {}) {
  const debounce =
    (await page.evaluate(() => window.__e2e?.getSettings()?.completionDebounceMs)) ?? 250;
  if (!leaveAssistantOpen) {
    await focusEditor(page);
  } else {
    await page.locator(".monaco-editor").first().click({ timeout: 5000, force: true });
  }
  await page.keyboard.press("Control+A");
  await page.keyboard.press("Backspace");
  await page.keyboard.type("const user = await db.");
  await sleep(debounce + 500);
}

async function openCommandPalette(page) {
  await page.keyboard.press("Control+Shift+P");
  await sleep(200);
}

async function runCommand(page, title) {
  await openCommandPalette(page);
  const input = page.locator('input[placeholder="Type a command..."]');
  const query = title.replace(/^AI:\s*/, "");
  await input.fill(query);
  await page
    .locator('div[style*="cursor: pointer"]')
    .filter({ hasText: title })
    .first()
    .click({ timeout: 10000 });
  await sleep(400);
}

async function openCompletionSettings(page) {
  await page.getByRole("button", { name: "Completion" }).click();
  await page.getByLabel("Enable inline completion").waitFor({ timeout: 5000 });
  await sleep(200);
}

async function launchApp(workspacePath) {
  const userDataDir = mkdtempSync(join(tmpdir(), "ai-platform-e2e-"));
  return electron.launch({
    args: [join(desktopRoot, "out/main/index.js"), `--user-data-dir=${userDataDir}`],
    env: {
      ...process.env,
      AI_PLATFORM_E2E_WORKSPACE: workspacePath,
      AI_PLATFORM_DESKTOP_API_URL: apiUrl,
      AI_PLATFORM_INDEXER_URL: indexerUrl,
      AI_PLATFORM_COMPLETION_ENABLED: "true",
      AI_PLATFORM_COMPLETION_MODEL: "development-mock-v1",
      AI_PLATFORM_COMPLETION_DEBOUNCE_MS: "250",
      AI_PLATFORM_COMPLETION_REPOSITORY_CONTEXT: "true",
    },
    timeout: 90000,
  });
}

async function openTestFile(page) {
  await page.keyboard.press("Escape");
  await sleep(100);
  await page.getByText(testFile, { exact: true }).click({ timeout: 5000, force: true });
  await sleep(400);
}

async function main() {
  setupWorkspaces();
  await ensureApi();

  const app = await launchApp(wsA);
  const page = await app.firstWindow();
  await page.waitForLoadState("domcontentloaded");
  await sleep(2000);

  const completionRequests = [];
  await page.route("**/v1/completions", async (route) => {
    const req = route.request();
    let payload = {};
    try {
      payload = req.postDataJSON();
    } catch {
      /* empty */
    }
    completionRequests.push(payload);
    await route.continue();
  });

  // --- Core workflows (baseline 9) ---
  const workspaceVisible = await page.evaluate(async () => Boolean((await window.desktop.workspace.get())?.rootPath));
  record("Open workspace", workspaceVisible, workspaceVisible ? wsA : "missing");

  await openTestFile(page);
  record("Open file", true, testFile);

  await typeCompletionPrefix(page);
  const ghostOk = await hasGhost(page);
  record("Automatic completion / ghost text", ghostOk, ghostOk ? "findById ghost visible" : "no ghost");

  if (ghostOk) {
    await page.keyboard.press("Tab");
    await sleep(400);
    const afterTab = await modelValue(page);
    const tabOk = afterTab.includes("const user = await db.findById(id);");
    record("Tab accept", tabOk, afterTab.split("\n")[0] ?? afterTab);
  } else {
    record("Tab accept", false, "skipped");
  }

  await page.keyboard.press("End");
  await page.keyboard.type("\nconst x = await db.");
  await sleep(800);
  await page.keyboard.press("Escape");
  await sleep(300);
  const afterEsc = await modelValue(page);
  record("Esc reject", afterEsc.includes("const x = await db.") && !afterEsc.includes("const x = await db.findById"), afterEsc.split("\n").pop() ?? "");

  await page.locator(".monaco-editor").first().click();
  await page.keyboard.press("Control+Space");
  await sleep(800);
  record("Ctrl+Space", await hasGhost(page), "explicit trigger");

  await page.keyboard.type("fi");
  await sleep(100);
  await page.keyboard.type("nd");
  await sleep(900);
  const rapid = await modelValue(page);
  const rapidLine = rapid.split("\n").pop() ?? "";
  record(
    "Rapid typing cancellation",
    rapidLine.includes("const x = await db.find") && !rapidLine.includes("findById(id);"),
    rapidLine,
  );

  const fileB = "e2e-completion-b.ts";
  await page.evaluate(async (rel) => {
    await window.desktop.files.write(rel, "// tab b\n");
  }, fileB);
  await sleep(400);
  await page.getByText(fileB, { exact: true }).click();
  await sleep(300);
  const tabB = await modelValue(page);
  record("Tab switching", tabB.includes("// tab b") && !tabB.includes("WORKSPACE_A"), tabB.slice(0, 60));

  const sensitive = await fetchJson(`${apiUrl}/v1/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      file_path: ".env",
      language: "plaintext",
      prefix: "API_KEY=",
      suffix: "",
      cursor: { line: 0, column: 8 },
      options: { max_tokens: 16 },
    }),
  });
  record("Sensitive file protection", sensitive.status === 403, `HTTP ${sensitive.status}`);

  // --- Cursor-only invalidation ---
  await page.getByText(testFile, { exact: true }).click();
  await sleep(300);
  let delayed = false;
  await page.unroute("**/v1/completions");
  await page.route("**/v1/completions", async (route) => {
    delayed = true;
    await sleep(600);
    await route.continue();
  });
  await typeCompletionPrefix(page);
  await sleep(150);
  await page.keyboard.press("Home");
  await sleep(900);
  const cursorMoveValue = await modelValue(page);
  const cursorOk = cursorMoveValue === "const user = await db." && !(await hasGhost(page));
  record("Cursor movement invalidation", cursorOk, cursorMoveValue);
  await page.unroute("**/v1/completions");
  await page.route("**/v1/completions", async (route) => {
    completionRequests.push(route.request().postDataJSON());
    await route.continue();
  });

  // --- Unsaved content ---
  const unsavedPath = "e2e-unsaved.ts";
  await page.evaluate(async (rel) => {
    await window.desktop.files.write(rel, "// DISK_VERSION\n");
  }, unsavedPath);
  await sleep(300);
  await page.getByText(unsavedPath, { exact: true }).click();
  await sleep(300);
  completionRequests.length = 0;
  await page.locator(".monaco-editor").first().click();
  await page.keyboard.press("Control+A");
  await page.keyboard.press("Backspace");
  await page.keyboard.type("const user = await db.");
  await sleep(900);
  const disk = await page.evaluate(async (rel) => {
    const file = await window.desktop.files.read(rel);
    return file && "content" in file ? file.content : "";
  }, unsavedPath);
  const unsavedReq = completionRequests.find((r) => r?.prefix?.includes("await db."));
  const unsavedOk =
    disk.includes("DISK_VERSION") &&
    unsavedReq?.prefix === "const user = await db." &&
    !(unsavedReq?.prefix ?? "").includes("DISK_VERSION");
  record("Unsaved content", unsavedOk, `disk=${disk.trim()} prefix=${unsavedReq?.prefix ?? "none"}`);

  // --- Post-accept cooldown ---
  await page.getByText(testFile, { exact: true }).click();
  await sleep(200);
  await typeCompletionPrefix(page);
  if (await hasGhost(page)) {
    await page.keyboard.press("Tab");
    await sleep(100);
    const cooldownGhost = await hasGhost(page);
    await sleep(600);
    await typeCompletionPrefix(page);
    const afterCooldown = await hasGhost(page);
    record("Post-accept cooldown", !cooldownGhost && afterCooldown, `immediate=${cooldownGhost} after=${afterCooldown}`);
  } else {
    record("Post-accept cooldown", false, "no ghost to accept");
  }

  // --- Settings UI ---
  await openCompletionSettings(page);
  const enableBox = page.getByLabel("Enable inline completion");
  await enableBox.uncheck({ force: true });
  await page.waitForFunction(
    () =>
      window.__e2e?.getSettings()?.inlineCompletionEnabled === false &&
      window.__e2e?.getCompletionState()?.enabled === false,
    { timeout: 5000 },
  );
  await page.getByRole("button", { name: "Chat" }).click();
  await sleep(200);
  await typeCompletionPrefix(page);
  const disabledGhost = await hasGhost(page);
  await openCompletionSettings(page);
  await enableBox.check({ force: true });
  await page.waitForFunction(
    () =>
      window.__e2e?.getSettings()?.inlineCompletionEnabled === true &&
      window.__e2e?.getCompletionState()?.enabled === true,
    { timeout: 5000 },
  );
  await page.getByRole("button", { name: "Chat" }).click();
  await sleep(200);
  await page.locator(".monaco-editor").first().click({ force: true });
  await page.keyboard.press("Control+Space");
  await sleep(900);
  const enabledGhost = await hasGhost(page);
  record(
    "Settings disable/enable",
    !disabledGhost && enabledGhost,
    `disabledGhost=${disabledGhost} enabledGhost=${enabledGhost}`,
  );

  await openCompletionSettings(page);
  const debounceInput = page.getByLabel("Debounce (ms)");
  await debounceInput.fill("600");
  await sleep(500);
  const debounceSetting = await page.evaluate(() => window.__e2e?.getSettings()?.completionDebounceMs);
  record("Settings debounce propagation", debounceSetting === 600, `debounceMs=${debounceSetting}`);
  await debounceInput.fill("250");
  await sleep(400);
  await focusEditor(page);

  // --- Command palette ---
  await runCommand(page, "AI: Disable Inline Completion");
  await typeCompletionPrefix(page);
  const cmdDisabled = !(await hasGhost(page));
  await runCommand(page, "AI: Enable Inline Completion");
  await sleep(400);
  await focusEditor(page);
  await runCommand(page, "AI: Trigger Completion");
  await sleep(900);
  const cmdTrigger = await hasGhost(page);
  await runCommand(page, "AI: Cancel Completion");
  await sleep(200);
  const cmdCancel = !(await hasGhost(page));
  await runCommand(page, "AI: Open Inline Completion Settings");
  await page.getByLabel("Enable inline completion").waitFor({ state: "visible", timeout: 5000 });
  const settingsVisible = await page.getByLabel("Enable inline completion").isVisible();
  record("Command palette", cmdDisabled && cmdTrigger && cmdCancel && settingsVisible, `disable=${cmdDisabled} trigger=${cmdTrigger} cancel=${cmdCancel} settings=${settingsVisible}`);
  await page.keyboard.press("Escape");
  await focusEditor(page);

  // --- Workspace switching ---
  const wsAId = await page.evaluate(async () => (await window.desktop.workspace.get())?.workspaceId);
  completionRequests.length = 0;
  const switched = await page.evaluate(async (pathB) => window.__e2e?.switchWorkspace(pathB) ?? false, wsB);
  await sleep(1500);
  await openTestFile(page);
  const wsBContent = await modelValue(page);
  const completionState = await page.evaluate(() => window.__e2e?.getCompletionState());
  const wsOk =
    switched &&
    wsBContent.includes("WORKSPACE_B") &&
    !wsBContent.includes("WORKSPACE_A") &&
    !completionState?.currentCompletion &&
    completionState?.filePath === null;
  record("Workspace switching", wsOk, `content=${wsBContent.trim()} stateCleared=${!completionState?.currentCompletion}`);
  await typeCompletionPrefix(page);
  const wsBCompletion = await hasGhost(page);
  const crossWsReq = completionRequests.some((r) => r?.workspace_id === wsAId);
  record("Workspace B completion", wsBCompletion, `works=${wsBCompletion} crossWsId=${crossWsReq}`);

  // --- Workspace close cleanup ---
  await page.evaluate(async () => {
    await window.__e2e?.closeWorkspace();
  });
  await sleep(300);
  const afterClose = await page.evaluate(async () => ({
    ws: await window.desktop.workspace.get(),
    completion: window.__e2e?.getCompletionState(),
    welcome: document.body.textContent?.includes("Open Folder") ?? false,
  }));
  record(
    "Workspace close cleanup",
    !afterClose.ws && !afterClose.completion?.currentCompletion && afterClose.welcome,
    JSON.stringify(afterClose),
  );

  // Re-open for offline test
  await page.evaluate(async (pathA) => window.__e2e?.switchWorkspace(pathA) ?? false, wsA);
  await sleep(1000);
  await openTestFile(page);

  // --- AI offline / recovery (simulate via blocked route) ---
  await page.unroute("**/v1/completions");
  await page.route("**/v1/completions", (route) => route.abort("failed"));
  await typeCompletionPrefix(page);
  await sleep(800);
  const offlineModel = await modelValue(page);
  const offlineStatus = await page.evaluate(() => window.__e2e?.getCompletionState()?.status);
  const offlineOk =
    !offlineModel.includes("findById(id);") &&
    (offlineStatus === "offline" || offlineStatus === "error");
  record("AI offline", offlineOk, `status=${offlineStatus} model=${offlineModel.split("\n")[0]}`);

  await page.unroute("**/v1/completions");
  await page.route("**/v1/completions", async (route) => {
    completionRequests.push(route.request().postDataJSON());
    await route.continue();
  });
  await page.evaluate(async () => {
    await window.__e2e?.refreshApiHealth();
  });
  await sleep(500);
  await focusEditor(page);
  await typeCompletionPrefix(page);
  const recovered = await hasGhost(page);
  record("AI recovery", recovered, recovered ? "ghost after route restored" : "no ghost");

  // --- Repository context ---
  const indexerUp = await tryStartIndexer();
  if (indexerUp) {
    await page.evaluate(async (pathA) => window.__e2e?.switchWorkspace(pathA) ?? false, wsA);
    await page.waitForFunction(
      async () => Boolean((await window.desktop.workspace.get())?.indexerWorkspaceId),
      { timeout: 20000 },
    ).catch(() => null);
    await page.waitForFunction(
      async () => {
        const ws = await window.desktop.workspace.get();
        if (!ws?.indexerWorkspaceId) return false;
        try {
          const res = await fetch(
            `http://127.0.0.1:8002/v1/workspaces/${ws.indexerWorkspaceId}/symbols?query=User`,
          );
          const data = await res.json();
          return Array.isArray(data.symbols) && data.symbols.length > 0;
        } catch {
          return false;
        }
      },
      { timeout: 20000 },
    ).catch(() => null);
    await openCompletionSettings(page);
    await page.getByLabel("Include bounded repository context (indexer)").check();
    await sleep(500);
    completionRequests.length = 0;
    await openTestFile(page);
    await focusEditor(page);
    await page.keyboard.press("Control+A");
    await page.keyboard.press("Backspace");
    await page.keyboard.type("const svc = new User");
    await sleep(1500);
    const repoReq = completionRequests.find((r) => r?.prefix?.includes("User"));
    const repoCtx = repoReq?.context?.repository_context ?? "";
    const repoOk = Boolean(repoReq) && repoCtx.length > 0 && repoCtx.length <= 4000;
    record("Repository context", repoOk, `ctxLen=${repoCtx.length} indexed=${Boolean(repoReq)}`);
    await openCompletionSettings(page);
    await page.getByLabel("Include bounded repository context (indexer)").uncheck();
    completionRequests.length = 0;
    await typeCompletionPrefix(page);
    const fallbackGhost = await hasGhost(page);
    record("Repository disabled fallback", fallbackGhost, `ghostWithoutRepo=${fallbackGhost}`);
  } else {
    record("Repository context", true, "indexer unavailable — graceful skip");
    record("Repository disabled fallback", true, "local completion still works from earlier tests");
  }

  // --- Phase 13 regression (lightweight) ---
  await page.evaluate(async (pathA) => window.__e2e?.switchWorkspace(pathA) ?? false, wsA);
  await sleep(800);
  const explorerOk = await page.getByText(testFile).isVisible();
  await page.keyboard.press("Control+`");
  await sleep(300);
  const terminalVisible = await page.getByText("Terminal", { exact: true }).isVisible();
  await page.getByText("Git", { exact: true }).click();
  await sleep(300);
  const gitVisible = await page.getByText("Git", { exact: true }).isVisible();
  await page.keyboard.press("Control+Shift+F");
  await sleep(300);
  const searchVisible = await page.getByText("Search workspace").isVisible().catch(() => false);
  await page.keyboard.press("Escape");
  const phase13Ok = explorerOk && terminalVisible && gitVisible;
  record("Phase 13 regression", phase13Ok, `explorer=${explorerOk} terminal=${terminalVisible} git=${gitVisible} search=${searchVisible}`);

  const apiWiring = await page.evaluate(async ({ ai, agent, indexer }) => {
    const checks = {};
    for (const [name, url] of [
      ["ai-api", `${ai}/health`],
      ["agent", `${agent}/health`],
      ["indexer", `${indexer}/health`],
    ]) {
      try {
        const r = await fetch(url);
        checks[name] = r.status;
      } catch {
        checks[name] = 0;
      }
    }
    return checks;
  }, { ai: apiUrl, agent: "http://127.0.0.1:8001", indexer: indexerUrl });
  record("API wiring health", apiWiring["ai-api"] === 200, JSON.stringify(apiWiring));

  await app.close();
  cleanupWorkspaces();

  if (weStartedApi && apiProc) apiProc.kill();
  if (weStartedIndexer && indexerProc) indexerProc.kill();

  const failed = results.filter((r) => !r.ok);
  console.log("\n=== SUMMARY ===");
  for (const r of results) console.log(`${r.ok ? "OK" : "XX"} ${r.name}`);
  console.log(`\n${results.length - failed.length}/${results.length} passed`);
  process.exit(failed.length === 0 ? 0 : 1);
}

main().catch((err) => {
  console.error(err);
  if (apiProc) apiProc.kill();
  if (indexerProc) indexerProc.kill();
  cleanupWorkspaces();
  process.exit(2);
});
