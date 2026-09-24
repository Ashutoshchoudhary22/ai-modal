import { cancelActiveCompletion, triggerActiveCompletion } from "../features/completion/completionBridge";
import { useCompletionStore } from "../features/completion/completionStore";
import { useEditorStore } from "../state/editorStore";
import { useSettingsStore } from "../state/settingsStore";
import { useWorkspaceStore } from "../state/workspaceStore";

export interface E2EBridge {
  switchWorkspace: (rootPath: string) => Promise<boolean>;
  closeWorkspace: () => Promise<void>;
  getModelValue: () => string;
  getCompletionState: () => ReturnType<typeof useCompletionStore.getState>;
  getSettings: () => ReturnType<typeof useSettingsStore.getState>["settings"];
  refreshApiHealth: () => Promise<void>;
  setInlineCompletionEnabled: (enabled: boolean) => Promise<void>;
  triggerCompletion: () => void;
  cancelCompletion: () => void;
  openAssistantCompletionSettings: () => Promise<void>;
}

export function installE2EBridge(): void {
  const bridge: E2EBridge = {
    async switchWorkspace(rootPath: string) {
      cancelActiveCompletion();
      await window.desktop.workspace.close();
      useWorkspaceStore.getState().setWorkspace(null);
      useEditorStore.getState().resetWorkspace();
      const result = await window.desktop.workspace.openPath(rootPath);
      if (!result || typeof result !== "object" || !("rootPath" in result)) {
        return false;
      }
      useWorkspaceStore.getState().setWorkspace(result);
      return true;
    },
    async closeWorkspace() {
      cancelActiveCompletion();
      await window.desktop.workspace.close();
      useWorkspaceStore.getState().setWorkspace(null);
      useEditorStore.getState().resetWorkspace();
    },
    getModelValue() {
      return window.__monacoActiveEditor__?.getModel()?.getValue() ?? "";
    },
    getCompletionState() {
      return useCompletionStore.getState();
    },
    getSettings() {
      return useSettingsStore.getState().settings;
    },
    async refreshApiHealth() {
      await useSettingsStore.getState().refreshHealth();
    },
    async setInlineCompletionEnabled(enabled: boolean) {
      await useSettingsStore.getState().updateSettings({ inlineCompletionEnabled: enabled });
      useCompletionStore.getState().setEnabled(enabled);
      if (!enabled) cancelActiveCompletion();
    },
    triggerCompletion() {
      triggerActiveCompletion();
    },
    cancelCompletion() {
      cancelActiveCompletion();
    },
    async openAssistantCompletionSettings() {
      const { useAssistantStore } = await import("../state/assistantStore");
      useAssistantStore.getState().setMode("completion");
    },
  };
  (window as Window & { __e2e?: E2EBridge }).__e2e = bridge;
}
