import type { CompletionController } from "./CompletionController";

let activeController: CompletionController | null = null;

export function setActiveCompletionController(controller: CompletionController | null): void {
  activeController = controller;
}

export function cancelActiveCompletion(): void {
  activeController?.cancel();
  const editor = (window as Window & {
    __monacoActiveEditor__?: { trigger: (s: string, a: string, p: unknown) => void };
  }).__monacoActiveEditor__;
  editor?.trigger("ai-completion", "editor.action.inlineSuggest.hide", {});
}

export function triggerActiveCompletion(): void {
  const editor = (window as Window & {
    __monacoActiveEditor__?: {
      focus: () => void;
      trigger: (s: string, a: string, p: unknown) => void;
    };
  }).__monacoActiveEditor__;
  if (!editor) return;
  editor.focus();
  editor.trigger("ai-completion", "editor.action.inlineSuggest.trigger", {});
}
