import { useCallback } from "react";
import { useEditorStore, isUntitledPath } from "../../state/editorStore";
import { useWorkspaceStore } from "../../state/workspaceStore";
import { useSettingsStore } from "../../state/settingsStore";
import { useNotificationStore } from "../../state/notificationStore";

function isError(v: unknown): boolean {
  return typeof v === "object" && v !== null && "code" in v;
}

export function useFileMenuActions() {
  const notify = useNotificationStore((s) => s.notify);
  const autoSave = useSettingsStore((s) => s.settings?.autoSave ?? false);
  const updateSettings = useSettingsStore((s) => s.updateSettings);
  const workspace = useWorkspaceStore((s) => s.workspace);
  const recents = useWorkspaceStore((s) => s.recents);
  const hasActiveEditor = useEditorStore((s) => Boolean(s.activeTab));
  const hasDirtyTabs = useEditorStore((s) =>
    s.tabs.some((t) => t.dirty || isUntitledPath(t.path)),
  );
  const mod = window.desktop.platform.isMac ? "Cmd" : "Ctrl";

  const saveTab = useCallback(
    async (path: string, content: string, promptPath?: string) => {
      if (isUntitledPath(path) || promptPath) {
        const dialog = await window.desktop.window.saveFileDialog(promptPath);
        if (dialog.canceled || !dialog.path) return false;
        const result = await window.desktop.files.write(dialog.path, content);
        if (isError(result)) {
          notify("error", (result as { message: string }).message);
          return false;
        }
        const { tabs, closeTab, openTab, markClean } = useEditorStore.getState();
        const tab = tabs.find((t) => t.path === path);
        closeTab(path);
        openTab(dialog.path, content, tab?.language);
        markClean(dialog.path);
        notify("success", `Saved ${dialog.path}`);
        return true;
      }
      const result = await window.desktop.files.write(path, content);
      if (isError(result)) {
        notify("error", (result as { message: string }).message);
        return false;
      }
      useEditorStore.getState().markClean(path);
      notify("success", `Saved ${path}`);
      return true;
    },
    [notify],
  );

  const saveActive = useCallback(async () => {
    const { activeTab, tabs } = useEditorStore.getState();
    const tab = tabs.find((t) => t.path === activeTab);
    if (!tab) {
      notify("error", "No file open");
      return;
    }
    await saveTab(tab.path, tab.content);
  }, [notify, saveTab]);

  const saveAll = useCallback(async () => {
    const { tabs } = useEditorStore.getState();
    const dirty = tabs.filter((t) => t.dirty || isUntitledPath(t.path));
    if (dirty.length === 0) {
      notify("success", "No unsaved files");
      return;
    }
    for (const tab of dirty) {
      const ok = await saveTab(tab.path, tab.content);
      if (!ok && isUntitledPath(tab.path)) break;
    }
  }, [notify, saveTab]);

  const openWorkspace = useCallback(async (rootPath?: string) => {
    const result = rootPath
      ? await window.desktop.workspace.openPath(rootPath)
      : await window.desktop.workspace.open();
    if (isError(result)) {
      if ((result as { code: string }).code !== "CANCELLED") {
        notify("error", (result as { message: string }).message);
      }
      return;
    }
    useWorkspaceStore.getState().setWorkspace(result);
    const info = await window.desktop.workspace.getProjectInfo();
    useWorkspaceStore.getState().setProjectInfo(info);
  }, [notify]);

  const actions = {
    mod,
    autoSave,
    newTextFile: () => useEditorStore.getState().newUntitled(),
    newWindow: () => void window.desktop.window.newWindow(),
    newAgentsWindow: () => void window.desktop.window.newWindow(),
    newWindowDefaultProfile: () => void window.desktop.window.newWindow(),
    openFile: async () => {
      const result = await window.desktop.window.openFileDialog();
      if (result.canceled || !result.path || result.content == null) return;
      useEditorStore.getState().openTab(result.path, result.content);
    },
    openFolder: () => void openWorkspace(),
    openWorkspaceFile: async () => {
      const result = await window.desktop.window.openWorkspaceFileDialog();
      if (result.canceled || !result.path) return;
      await openWorkspace(result.path);
    },
    openRecent: (path: string) => void openWorkspace(path),
    addFolderToWorkspace: () =>
      notify("error", "Multi-root workspaces are not supported yet"),
    saveWorkspaceAs: () => notify("error", "Save Workspace As is not available yet"),
    duplicateWorkspace: () => notify("error", "Duplicate Workspace is not available yet"),
    save: () => void saveActive(),
    saveAs: async () => {
      const { activeTab, tabs } = useEditorStore.getState();
      const tab = tabs.find((t) => t.path === activeTab);
      if (!tab) {
        notify("error", "No file open");
        return;
      }
      await saveTab(tab.path, tab.content, isUntitledPath(tab.path) ? undefined : tab.path);
    },
    saveAll: () => void saveAll(),
    toggleAutoSave: () => void updateSettings({ autoSave: !autoSave }),
    openPreferences: async () => {
      const { useAssistantStore } = await import("../../state/assistantStore");
      useAssistantStore.getState().setMode("completion");
    },
    toggleTheme: async () => {
      const settings = useSettingsStore.getState().settings;
      const next = settings?.theme === "light" ? "dark" : "light";
      await updateSettings({ theme: next });
      document.documentElement.setAttribute("data-theme", next);
    },
    revertFile: async () => {
      const { activeTab, tabs, updateContent, markClean } = useEditorStore.getState();
      const tab = tabs.find((t) => t.path === activeTab);
      if (!tab || isUntitledPath(tab.path)) {
        notify("error", "Cannot revert untitled file");
        return;
      }
      const result = await window.desktop.files.read(tab.path);
      if (isError(result)) {
        notify("error", (result as { message: string }).message);
        return;
      }
      updateContent(tab.path, (result as { content: string }).content);
      markClean(tab.path);
      notify("success", "File reverted");
    },
    closeEditor: () => {
      const { activeTab, closeTab } = useEditorStore.getState();
      if (!activeTab) return;
      closeTab(activeTab);
    },
    closeFolder: async () => {
      await window.desktop.workspace.close();
      useWorkspaceStore.getState().setWorkspace(null);
      useEditorStore.getState().resetWorkspace();
    },
    closeWindow: () => void window.desktop.window.closeWindow(),
    exit: () => void window.desktop.window.quit(),
    hasWorkspace: Boolean(workspace),
    hasActiveEditor,
    hasDirtyTabs,
    recents,
  };

  return actions;
}
