const trim = (url: string) => url.replace(/\/+$/, "");

export async function searchWorkspace(
  indexerUrl: string,
  workspaceId: string,
  query: string,
  limit = 20,
): Promise<Array<{ path: string; score?: number }>> {
  const res = await fetch(`${trim(indexerUrl)}/v1/workspaces/${workspaceId}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  const data = (await res.json()) as { results?: Array<{ path: string; score?: number }> };
  return data.results ?? [];
}

export async function searchSymbols(
  indexerUrl: string,
  workspaceId: string,
  query: string,
): Promise<Array<{ name: string; path: string; kind: string }>> {
  const res = await fetch(
    `${trim(indexerUrl)}/v1/workspaces/${workspaceId}/symbols?query=${encodeURIComponent(query)}`,
  );
  if (!res.ok) throw new Error(`Symbol search failed: ${res.status}`);
  const data = (await res.json()) as {
    symbols?: Array<{ name: string; path: string; kind: string }>;
  };
  return data.symbols ?? [];
}
