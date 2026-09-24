/**
 * Phase 14 live Monaco inline completion verification.
 * Requires AI API on http://127.0.0.1:8000 with /v1/completions.
 */
import { _electron as electron } from "playwright";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { writeFileSync, unlinkSync, existsSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const desktopRoot = join(__dirname, "..");
const repoRoot = join(desktopRoot, "..", "..");
const testFile = "e2e-completion-verify.ts";
const testFileAbs = join(repoRoot, testFile);

const results = [];

function record(name, ok, evidence) {
  results.push({ name, ok, evidence });
  console.log(`${ok ? "PASS" : "FAIL"} ${name}: ${evidence}`);
}

async function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function main() {
  writeFileSync(testFileAbs, "", "utf-8");

  const app = await electron.launch({
    args: [join(desktopRoot, "out/main/index.js")],
    env: {
      ...process.env,
      AI_PLATFORM_E2E_WORKSPACE: repoRoot,
      AI_PLATFORM_DESKTOP_API_URL: "http://127.0.0.1:8000",
      AI_PLATFORM_COMPLETION_ENABLED: "true",
      AI_PLATFORM_COMPLETION_MODEL: "development-mock-v1",
      AI_PLATFORM_COMPLETION_DEBOUNCE_MS: "250",
      AI_PLATFORM_COMPLETION_REPOSITORY_CONTEXT: "false",
    },
    timeout: 60000,
  });

  const page = await app.firstWindow();
  await page.waitForLoadState("domcontentloaded");
  await sleep(2000);

  const workspaceVisible = await page.evaluate(async () => {
    const ws = await window.desktop.workspace.get();
    return Boolean(ws?.rootPath);
  });
  record("Open workspace", workspaceVisible, workspaceVisible ? "main+renderer workspace synced" : "workspace missing");

  await page.evaluate(async (relPath) => {
    await window.desktop.files.write(relPath, "");
  }, testFile);
  await sleep(500);

  const fileClicked = await page.getByText(testFile, { exact: true }).click({ timeout: 5000 }).then(() => true).catch(() => false);
  record("Open file", fileClicked, fileClicked ? `opened ${testFile}` : "could not click file in explorer");

  const editor = page.locator(".monaco-editor");
  await editor.click({ timeout: 5000 });
  await page.keyboard.type("const user = await db.");
  await sleep(800);

  const editorState = await page.evaluate(() => {
    const line = document.querySelector(".monaco-editor .view-lines");
    const ghost =
      document.querySelector(".ghost-text") ??
      document.querySelector("[class*='ghost-text']") ??
      document.querySelector(".inline-completion-text");
    return {
      lineText: line?.textContent ?? "",
      ghostText: ghost?.textContent ?? null,
    };
  });

  const hasGhost =
    editorState.ghostText?.includes("findById") ||
    editorState.lineText.includes("findById");
  record(
    "Ghost text",
    hasGhost,
    hasGhost
      ? `visible: ghost=${editorState.ghostText ?? editorState.lineText}`
      : `line=${editorState.lineText}`,
  );

  if (hasGhost) {
    await page.keyboard.press("Tab");
    await sleep(400);
    const afterTab = await page.evaluate(() => {
      const editor = window.__monacoActiveEditor__;
      return editor?.getModel()?.getValue() ?? "";
    });
    const accepted =
      afterTab.includes("const user = await db.findById(id);") &&
      !afterTab.includes("findById(id);()");
    record("Tab accept", accepted, afterTab);
  } else {
    record("Tab accept", false, "skipped — no ghost text");
  }

  await page.keyboard.press("End");
  await page.keyboard.type("\nconst x = await db.");
  await sleep(800);
  await page.keyboard.press("Escape");
  await sleep(300);
  const afterEsc = await page.evaluate(() => window.__monacoActiveEditor__?.getModel()?.getValue() ?? "");
  const escOk = afterEsc.includes("const x = await db.") && !afterEsc.includes("const x = await db.findById");
  record("Esc reject", escOk, afterEsc);

  await editor.click();
  await page.keyboard.press("Control+Space");
  await sleep(800);
  const afterCtrlSpace = await page.evaluate(() => {
    const line = document.querySelector(".monaco-editor .view-lines")?.textContent ?? "";
    const ghost = document.querySelector(".ghost-text, [class*='ghost-text']")?.textContent ?? "";
    return `${line}${ghost}`;
  });
  record(
    "Ctrl+Space",
    afterCtrlSpace.includes("findById"),
    afterCtrlSpace,
  );

  await page.keyboard.type("fi");
  await sleep(100);
  await page.keyboard.type("nd");
  await sleep(900);
  const rapidTyping = await page.evaluate(() => window.__monacoActiveEditor__?.getModel()?.getValue() ?? "");
  record(
    "Rapid typing cancellation",
    rapidTyping.includes("const x = await db.") && !rapidTyping.includes("const x = await db.findById(id);"),
    rapidTyping.split("\n").pop() ?? "",
  );

  const fileB = "e2e-completion-b.ts";
  await page.evaluate(async (rel) => {
    await window.desktop.files.write(rel, "// tab b\n");
  }, fileB);
  await sleep(400);
  await page.getByText(fileB, { exact: true }).click();
  await sleep(300);
  const tabSwitch = await page.evaluate(() => ({
    active: window.__monacoActiveEditor__?.getModel()?.getValue() ?? "",
    file: window.__monacoActiveEditor__?.getModel()?.uri?.path ?? "",
  }));
  record(
    "Tab switching",
    tabSwitch.active.includes("// tab b") && !tabSwitch.active.includes("const x = await db.findById"),
    tabSwitch.active.slice(0, 80),
  );

  const sensitiveBlocked = await page.evaluate(async () => {
    const res = await fetch("http://127.0.0.1:8000/v1/completions", {
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
    return res.status;
  });
  record("Sensitive file protection", sensitiveBlocked === 403, `HTTP ${sensitiveBlocked}`);

  await app.close();
  if (existsSync(testFileAbs)) unlinkSync(testFileAbs);
  const fileBAbs = join(repoRoot, fileB);
  if (existsSync(fileBAbs)) unlinkSync(fileBAbs);

  const failed = results.filter((r) => !r.ok);
  console.log("\n=== SUMMARY ===");
  for (const r of results) console.log(`${r.ok ? "OK" : "XX"} ${r.name}`);
  process.exit(failed.length === 0 ? 0 : 1);
}

main().catch((err) => {
  console.error(err);
  process.exit(2);
});
