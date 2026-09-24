import {
  calculatePrefix,
  calculateSuffix,
  detectCurrentBlock,
  extractImports,
  extractNearbyCode,
} from "./completionUtils";
import type { CompletionContextPayload } from "./completionTypes";

export interface EditorSnapshot {
  filePath: string;
  language: string;
  content: string;
  line: number;
  column: number;
  offset: number;
  documentVersion: number;
  workspaceId?: string;
}

export function collectCompletionContext(
  snapshot: EditorSnapshot,
  contextLines: number,
  repositoryContext?: string,
): {
  prefix: string;
  suffix: string;
  context: CompletionContextPayload;
} {
  const prefix = calculatePrefix(snapshot.content, snapshot.offset);
  const suffix = calculateSuffix(snapshot.content, snapshot.offset);
  const nearby = extractNearbyCode(snapshot.content, snapshot.line, contextLines);
  const imports = extractImports(snapshot.content);
  const currentFunction = detectCurrentBlock(snapshot.content, snapshot.line);

  const context: CompletionContextPayload = {
    nearby_code: nearby,
    imports,
    current_function: currentFunction,
  };
  if (repositoryContext) {
    context.repository_context = repositoryContext.slice(0, 4000);
  }
  return { prefix, suffix, context };
}
