import { useCallback, useEffect, useState } from "react";
import { WelcomeScreen } from "./components/WelcomeScreen";
import { FileExplorer } from "./explorer/FileExplorer";
import { EditorTabs } from "./editor/EditorTabs";
import { MonacoEditor } from "./editor/MonacoEditor";
import { DiffReview } from "./editor/DiffReview";
import { AssistantPanel } from "./assistant/AssistantPanel";
import { BottomPanel } from "./components/BottomPanel";
import { StatusBar } from "./components/StatusBar";
import { CommandPalette } from "./components/CommandPalette";
import { SearchPanel } from "./components/SearchPanel";
import { Notifications } from "./components/Notifications";
import { useWorkspaceStore } from "./state/workspaceStore";
import { useSettingsStore } from "./state/settingsStore";
import { useEditorStore } from "./state/editorStore";
import { commandRegistry } from "./state/commands";
import { useNotificationStore } from "./state/notificationStore";

type BottomTab = "terminal" | "problems" | "output" | "git" | "agent" | "evaluation";

export default function App() {
  const workspace = useWorkspaceStore((s) => s.workspace);
  const loadSettings = useSettingsStore((s) => s.loadSettings);
  const refreshHealth = useSettingsStore((s) => s.refreshHealth);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [bottomTab, setBottomTab] = useState<BottomTab>("terminal");
  const [bottomCollapsed, setBottomCollapsed] = useState(false);
  const notify = useNotificationStore((s) => s.notify);

  useEffect(() => {
    void loadSettings();
    const recents = window.desktop.workspace.getRecents();
    void recents.then((r) => useWorkspaceStore.getState().setRecents(r));
    void window.desktop.workspace.get().then((ws) => {
      if (ws) useWorkspaceStore.getState().setWorkspace(ws);
    });
    const interval = setInterval(() => void refreshHealth(), 30000);
    return () => clearInterval(interval);
  }, [loadSettings, refreshHealth]);

  useEffect(() => {
    if (!workspace) return undefined;
    let active = true;
    const refreshWorkspace = async () => {
      const ws = await window.desktop.workspace.get();
      if (active && ws) useWorkspaceStore.getState().setWorkspace(ws);
    };
    void refreshWorkspace();
    const interval = setInterval(() => void refreshWorkspace(), 1500);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [workspace?.workspaceId]);

  useEffect(() => {
    if (!workspace) {
      import("./features/completion/completionBridge").then(({ cancelActiveCompletion }) =>
        cancelActiveCompletion(),
      );
      import("./features/completion/completionDocumentVersion").then(({ clearDocumentVersions }) =>
        clearDocumentVersions(),
      );
      useEditorStore.getState().resetWorkspace();
    }
  }, [workspace]);

  const saveActive = useCallback(async () => {
    const { activeTab, tabs, markClean } = useEditorStore.getState();
    const tab = tabs.find((t) => t.path === activeTab);
    if (!tab) return;
    const result = await window.desktop.files.write(tab.path, tab.content);
    if (result && typeof result === "object" && "code" in result) {
      notify("error", (result as { message: string }).message);
      return;
    }
    markClean(tab.path);
    notify("success", `Saved ${tab.path}`);
  }, [notify]);

  const saveAll = useCallback(async () => {
    const { tabs, markClean } = useEditorStore.getState();
    for (const tab of tabs.filter((t) => t.dirty)) {
      await window.desktop.files.write(tab.path, tab.content);
      markClean(tab.path);
    }
    notify("success", "All files saved");
  }, [notify]);

  useEffect(() => {
    const mod = window.desktop.platform.isMac ? "Cmd" : "Ctrl";
    commandRegistry.register({ id: "open-workspace", title: "Open Workspace", handler: async () => {
      const result = await window.desktop.workspace.open();
      if (result && "rootPath" in result) {
        useWorkspaceStore.getState().setWorkspace(result);
      }
    }});
    commandRegistry.register({ id: "save", title: "Save", shortcut: `${mod}+S`, handler: () => void saveActive() });
    commandRegistry.register({ id: "save-all", title: "Save All", shortcut: `${mod}+Shift+S`, handler: () => void saveAll() });
    commandRegistry.register({ id: "search", title: "Search", shortcut: `${mod}+Shift+F`, handler: () => setSearchOpen(true) });
    commandRegistry.register({ id: "command-palette", title: "Command Palette", shortcut: `${mod}+Shift+P`, handler: () => setCommandPaletteOpen(true) });
    commandRegistry.register({ id: "toggle-terminal", title: "Toggle Terminal", shortcut: `${mod}+\``, handler: () => {
      setBottomTab("terminal");
      setBottomCollapsed(false);
    }});
    commandRegistry.register({ id: "ask-ai", title: "Ask AI", handler: () => {} });
    commandRegistry.register({ id: "run-agent", title: "Run Agent", handler: () => {
      import("./state/assistantStore").then(({ useAssistantStore }) => useAssistantStore.getState().setMode("agent"));
    }});
    commandRegistry.register({ id: "git-status", title: "Git Status", handler: () => {
      setBottomTab("git");
      setBottomCollapsed(false);
    }});
    commandRegistry.register({ id: "evaluation", title: "Run Evaluation", handler: () => {
      setBottomTab("evaluation");
      setBottomCollapsed(false);
    }});
    commandRegistry.register({ id: "completion-enable", title: "AI: Enable Inline Completion", handler: () => {
      void useSettingsStore.getState().updateSettings({ inlineCompletionEnabled: true });
      import("./features/completion/completionStore").then(({ useCompletionStore }) =>
        useCompletionStore.getState().setEnabled(true),
      );
    }});
    commandRegistry.register({ id: "completion-disable", title: "AI: Disable Inline Completion", handler: () => {
      void useSettingsStore.getState().updateSettings({ inlineCompletionEnabled: false });
      import("./features/completion/completionStore").then(({ useCompletionStore }) =>
        useCompletionStore.getState().setEnabled(false),
      );
    }});
    commandRegistry.register({ id: "completion-settings", title: "AI: Open Inline Completion Settings", handler: () => {
      import("./state/assistantStore").then(({ useAssistantStore }) => useAssistantStore.getState().setMode("completion"));
    }});
    commandRegistry.register({ id: "completion-trigger", title: "AI: Trigger Completion", shortcut: `${mod}+Space`, handler: () => {
      import("./features/completion/completionBridge").then(({ triggerActiveCompletion }) => triggerActiveCompletion());
    }});
    commandRegistry.register({ id: "completion-cancel", title: "AI: Cancel Completion", shortcut: "Esc", handler: () => {
      import("./features/completion/completionBridge").then(({ cancelActiveCompletion }) => cancelActiveCompletion());
    }});
  }, [saveActive, saveAll]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const mod = window.desktop.platform.isMac ? e.metaKey : e.ctrlKey;
      if (mod && e.shiftKey && e.key === "P") {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
      if (mod && e.shiftKey && e.key === "F") {
        e.preventDefault();
        setSearchOpen(true);
      }
      if (mod && e.key === "s" && !e.shiftKey) {
        e.preventDefault();
        void saveActive();
      }
      if (mod && e.shiftKey && e.key === "S") {
        e.preventDefault();
        void saveAll();
      }
      if (mod && e.key === "`") {
        e.preventDefault();
        setBottomTab("terminal");
        setBottomCollapsed(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [saveActive, saveAll]);

  if (!workspace) {
    return (
      <>
        <WelcomeScreen />
        <Notifications />
      </>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ width: 240, flexShrink: 0 }}>
          <FileExplorer />
        </div>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", position: "relative" }}>
          <EditorTabs />
          <div style={{ flex: 1, overflow: "hidden" }}>
            <MonacoEditor />
          </div>
          <DiffReview />
        </div>
        <div style={{ width: 360, flexShrink: 0 }}>
          <AssistantPanel />
        </div>
      </div>
      <BottomPanel
        activeTab={bottomTab}
        onTabChange={setBottomTab}
        collapsed={bottomCollapsed}
        onToggleCollapse={() => setBottomCollapsed(!bottomCollapsed)}
        problems={[]}
      />
      <StatusBar />
      <CommandPalette open={commandPaletteOpen} onClose={() => setCommandPaletteOpen(false)} />
      <SearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} />
      <Notifications />
    </div>
  );
}
