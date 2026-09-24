const TRIGGER_CHARS = new Set([".", "(", "{", "[", "=", ":", ">", "\n"]);

const SENSITIVE_PATTERNS = [".env", ".pem", ".key", "credentials.", "secrets."];

function isSensitivePath(relativePath: string): boolean {
  const normalized = relativePath.replace(/\\/g, "/");
  const base = normalized.split("/").pop() ?? "";
  if (normalized.endsWith(".env.example")) return false;
  for (const pattern of SENSITIVE_PATTERNS) {
    if (pattern.endsWith(".")) {
      if (base.startsWith(pattern)) return true;
    } else if (base === pattern || normalized.includes(`/${pattern}`)) {
      return true;
    }
  }
  return false;
}

export function shouldTriggerCompletion(
  char: string,
  triggerOnTyping: boolean,
): boolean {
  if (!triggerOnTyping) return false;
  return TRIGGER_CHARS.has(char) || /\w/.test(char);
}

export function calculatePrefix(content: string, offset: number): string {
  return content.slice(0, offset);
}

export function calculateSuffix(content: string, offset: number): string {
  return content.slice(offset);
}

export function extractNearbyCode(
  content: string,
  line: number,
  contextLines: number,
): string {
  const lines = content.split("\n");
  const start = Math.max(0, line - contextLines);
  const end = Math.min(lines.length, line + contextLines + 1);
  return lines.slice(start, end).join("\n");
}

export function detectCurrentBlock(content: string, line: number): string | null {
  const lines = content.split("\n");
  let start = line;
  while (start > 0 && lines[start]?.trim() !== "") {
    if (/^(function|class|def|async|export|const|let|var)\b/.test(lines[start] ?? "")) break;
    start--;
  }
  const block = lines.slice(start, Math.min(lines.length, line + 20)).join("\n");
  return block.length > 0 ? block : null;
}

export function extractImports(content: string): string[] {
  const imports: string[] = [];
  for (const line of content.split("\n").slice(0, 100)) {
    if (/^\s*(import|from|#include|require\()/.test(line)) {
      imports.push(line.trim());
    }
  }
  return imports;
}

export function isCompletionAllowed(filePath: string, enabled: boolean): boolean {
  if (!enabled) return false;
  if (isSensitivePath(filePath)) return false;
  return true;
}

export function normalizeCompletion(text: string): string {
  return text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

export function deduplicateCompletion(text: string, prefix: string, suffix: string): string {
  let result = text;
  if (prefix && result.startsWith(prefix)) {
    result = result.slice(prefix.length);
  }
  if (suffix && result.endsWith(suffix)) {
    result = result.slice(0, -suffix.length);
  }
  return result;
}
