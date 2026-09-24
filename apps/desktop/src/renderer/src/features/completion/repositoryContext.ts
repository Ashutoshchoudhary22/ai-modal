import { searchSymbols, searchWorkspace } from "../../api/indexer";

const MAX_CONTEXT_CHARS = 4000;

function extractQueryToken(prefix: string): string | null {
  const match = prefix.match(/(?:^|[\s({[=,])([A-Za-z_$][\w$]*)$/);
  return match?.[1] ?? null;
}

export async function fetchRepositoryContext(
  indexerUrl: string,
  indexerWorkspaceId: string,
  prefix: string,
  signal?: AbortSignal,
): Promise<string | null> {
  const token = extractQueryToken(prefix);
  if (!token || token.length < 2) return null;

  try {
    const [symbols, paths] = await Promise.all([
      searchSymbols(indexerUrl, indexerWorkspaceId, token),
      searchWorkspace(indexerUrl, indexerWorkspaceId, token, 5),
    ]);
    if (signal?.aborted) return null;

    const parts: string[] = [];
    for (const sym of symbols.slice(0, 5)) {
      parts.push(`symbol ${sym.kind} ${sym.name} (${sym.path})`);
    }
    for (const hit of paths.slice(0, 3)) {
      parts.push(`file ${hit.path}`);
    }
    if (parts.length === 0) return null;
    return parts.join("\n").slice(0, MAX_CONTEXT_CHARS);
  } catch {
    return null;
  }
}
