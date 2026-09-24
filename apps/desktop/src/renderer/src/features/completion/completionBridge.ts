import type { CompletionController } from "./CompletionController";

let activeController: CompletionController | null = null;

export function setActiveCompletionController(controller: CompletionController | null): void {
  activeController = controller;
}

export function cancelActiveCompletion(): void {
  activeController?.cancel();
}
