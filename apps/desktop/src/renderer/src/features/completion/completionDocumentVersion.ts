const documentVersions = new Map<string, number>();

export function bumpDocumentVersion(filePath: string): number {
  const next = (documentVersions.get(filePath) ?? 0) + 1;
  documentVersions.set(filePath, next);
  return next;
}

export function getDocumentVersion(filePath: string): number {
  return documentVersions.get(filePath) ?? 0;
}

export function clearDocumentVersions(): void {
  documentVersions.clear();
}
