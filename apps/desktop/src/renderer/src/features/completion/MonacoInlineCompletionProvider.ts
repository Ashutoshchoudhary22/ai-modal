import type { Monaco } from "@monaco-editor/react";
import type { editor, languages } from "monaco-editor";
import { CompletionController } from "./CompletionController";
import { useCompletionStore } from "./completionStore";
import type { EditorSnapshot } from "./CompletionContextCollector";
import { bumpDocumentVersion, getDocumentVersion } from "./completionDocumentVersion";

export { bumpDocumentVersion, getDocumentVersion } from "./completionDocumentVersion";

export function registerInlineCompletionProvider(
  monaco: Monaco,
  controller: CompletionController,
  filePath: string,
  language: string,
  workspaceId?: string,
): languages.IDisposable {
  const provider: languages.InlineCompletionsProvider = {
    provideInlineCompletions: async (model, position, context, token) => {
      const store = useCompletionStore.getState();
      if (!store.enabled) return { items: [] };

      const offset = model.getOffsetAt(position);
      const snapshot: EditorSnapshot = {
        filePath,
        language,
        content: model.getValue(),
        line: position.lineNumber - 1,
        column: position.column - 1,
        offset,
        documentVersion: getDocumentVersion(filePath),
        workspaceId,
      };

      const kind = context.triggerKind === monaco.languages.InlineCompletionTriggerKind.Explicit
        ? "manual"
        : "automatic";

      const text = await controller.provide(snapshot, kind, token);
      if (!text || token.isCancellationRequested) return { items: [] };

      return {
        items: [
          {
            insertText: text,
            range: new monaco.Range(
              position.lineNumber,
              position.column,
              position.lineNumber,
              position.column,
            ),
          },
        ],
      };
    },
    freeInlineCompletions: () => {},
  };

  return monaco.languages.registerInlineCompletionsProvider(language, provider);
}

export function setupCompletionListeners(
  editor: editor.IStandaloneCodeEditor,
  controller: CompletionController,
  filePath: string,
): () => void {
  const model = editor.getModel();
  if (!model) return () => {};

  const contentDisposable = model.onDidChangeContent(() => {
    bumpDocumentVersion(filePath);
    controller.cancel();
  });

  return () => {
    contentDisposable.dispose();
    controller.dispose();
  };
}
