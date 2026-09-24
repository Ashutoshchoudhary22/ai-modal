import type { MenuDefinition, MenuItem } from "./menuTypes";
import type { useFileMenuActions } from "./useFileMenuActions";

type FileActions = ReturnType<typeof useFileMenuActions>;

export function buildFileMenu(actions: FileActions): MenuDefinition {
  const recentItems: MenuItem[] =
    actions.recents.length > 0
      ? actions.recents.map((r) => ({
          id: `recent-${r.rootPath}`,
          label: r.name,
          action: () => actions.openRecent(r.rootPath),
        }))
      : [{ id: "recent-empty", label: "No Recent Folders", disabled: true }];

  return {
    id: "file",
    label: "File",
    items: [
      { id: "new-text", label: "New Text File", shortcut: `${actions.mod}+N`, action: actions.newTextFile },
      { id: "new-window", label: "New Window", shortcut: `${actions.mod}+Shift+N`, action: actions.newWindow },
      {
        id: "new-agents-window",
        label: "New Agents Window",
        shortcut: `${actions.mod}+Alt+N`,
        action: actions.newAgentsWindow,
      },
      {
        id: "new-window-profile",
        label: "New Window with Profile",
        submenu: [
          { id: "profile-default", label: "Default", action: actions.newWindowDefaultProfile },
        ],
      },
      { id: "sep-1", separator: true },
      { id: "open-file", label: "Open File...", shortcut: `${actions.mod}+O`, action: actions.openFile },
      { id: "open-folder", label: "Open Folder...", shortcut: `${actions.mod}+K ${actions.mod}+O`, action: actions.openFolder },
      { id: "open-workspace-file", label: "Open Workspace from File...", action: actions.openWorkspaceFile },
      { id: "open-recent", label: "Open Recent", submenu: recentItems },
      { id: "sep-2", separator: true },
      {
        id: "add-folder",
        label: "Add Folder to Workspace...",
        disabled: !actions.hasWorkspace,
        action: actions.addFolderToWorkspace,
      },
      {
        id: "save-workspace",
        label: "Save Workspace As...",
        disabled: !actions.hasWorkspace,
        action: actions.saveWorkspaceAs,
      },
      {
        id: "duplicate-workspace",
        label: "Duplicate Workspace",
        disabled: !actions.hasWorkspace,
        action: actions.duplicateWorkspace,
      },
      { id: "sep-3", separator: true },
      {
        id: "save",
        label: "Save",
        shortcut: `${actions.mod}+S`,
        disabled: !actions.hasActiveEditor,
        action: actions.save,
      },
      {
        id: "save-as",
        label: "Save As...",
        shortcut: `${actions.mod}+Shift+S`,
        disabled: !actions.hasActiveEditor,
        action: actions.saveAs,
      },
      {
        id: "save-all",
        label: "Save All",
        shortcut: `${actions.mod}+K S`,
        disabled: !actions.hasDirtyTabs,
        action: actions.saveAll,
      },
      { id: "sep-4", separator: true },
      {
        id: "share",
        label: "Share",
        submenu: [{ id: "share-link", label: "Copy Link", disabled: true }],
      },
      { id: "sep-5", separator: true },
      {
        id: "auto-save",
        label: "Auto Save",
        checked: actions.autoSave,
        action: actions.toggleAutoSave,
      },
      {
        id: "preferences",
        label: "Preferences",
        submenu: [
          { id: "pref-settings", label: "Settings", action: actions.openPreferences },
          { id: "pref-theme", label: "Toggle Theme", action: actions.toggleTheme },
        ],
      },
      { id: "sep-6", separator: true },
      {
        id: "revert",
        label: "Revert File",
        disabled: !actions.hasActiveEditor,
        action: actions.revertFile,
      },
      {
        id: "close-editor",
        label: "Close Editor",
        shortcut: `${actions.mod}+F4`,
        disabled: !actions.hasActiveEditor,
        action: actions.closeEditor,
      },
      {
        id: "close-folder",
        label: "Close Folder",
        shortcut: `${actions.mod}+K F`,
        disabled: !actions.hasWorkspace,
        action: actions.closeFolder,
      },
      {
        id: "close-window",
        label: "Close Window",
        shortcut: "Alt+F4",
        action: actions.closeWindow,
      },
      { id: "sep-7", separator: true },
      { id: "exit", label: "Exit", action: actions.exit },
    ],
  };
}

export function buildEditMenu(actions: FileActions): MenuDefinition {
  return {
    id: "edit",
    label: "Edit",
    items: [
      { id: "undo", label: "Undo", shortcut: `${actions.mod}+Z`, disabled: true },
      { id: "redo", label: "Redo", shortcut: `${actions.mod}+Y`, disabled: true },
      { id: "sep-1", separator: true },
      { id: "find", label: "Find", shortcut: `${actions.mod}+F`, disabled: true },
      { id: "replace", label: "Replace", shortcut: `${actions.mod}+H`, disabled: true },
    ],
  };
}

export function buildViewMenu(): MenuDefinition {
  return {
    id: "view",
    label: "View",
    items: [
      { id: "command-palette", label: "Command Palette...", shortcut: "Ctrl+Shift+P", disabled: true },
      { id: "explorer", label: "Explorer", disabled: true },
      { id: "terminal", label: "Terminal", shortcut: "Ctrl+`", disabled: true },
    ],
  };
}

export function buildWindowMenu(actions: FileActions): MenuDefinition {
  return {
    id: "window",
    label: "Window",
    items: [
      { id: "new-window", label: "New Window", shortcut: `${actions.mod}+Shift+N`, action: actions.newWindow },
      { id: "close-window", label: "Close Window", shortcut: "Alt+F4", action: actions.closeWindow },
    ],
  };
}

export function buildHelpMenu(): MenuDefinition {
  return {
    id: "help",
    label: "Help",
    items: [
      {
        id: "docs",
        label: "Documentation",
        action: () => void window.desktop.window.openExternal("https://github.com"),
      },
    ],
  };
}
