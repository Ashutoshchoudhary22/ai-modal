/** Desktop main-process logging — never logs secrets. */

const SECRET_PATTERNS = [
  /api[_-]?key/i,
  /password/i,
  /authorization/i,
  /bearer\s+/i,
  /\.env\b/i,
];

function redact(message: string): string {
  let result = message;
  for (const pattern of SECRET_PATTERNS) {
    if (pattern.test(result)) {
      result = result.replace(pattern, "[REDACTED]");
    }
  }
  return result;
}

export const desktopLog = {
  info: (category: string, message: string) => {
    console.log(`[desktop:${category}] ${redact(message)}`);
  },
  warn: (category: string, message: string) => {
    console.warn(`[desktop:${category}] ${redact(message)}`);
  },
  error: (category: string, message: string) => {
    console.error(`[desktop:${category}] ${redact(message)}`);
  },
};
