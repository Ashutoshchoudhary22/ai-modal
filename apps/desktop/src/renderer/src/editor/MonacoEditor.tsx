import Editor, { type Monaco } from "@monaco-editor/react";

import { useEffect, useRef } from "react";

import { useEditorStore } from "../state/editorStore";

import { useSettingsStore } from "../state/settingsStore";

import { useWorkspaceStore } from "../state/workspaceStore";

import {
  CompletionController,
  type CompletionSettings,
} from "../features/completion/CompletionController";

import {

  registerInlineCompletionProvider,

  setupCompletionListeners,

} from "../features/completion/MonacoInlineCompletionProvider";

import { useCompletionStore } from "../features/completion/completionStore";
import { setActiveCompletionController } from "../features/completion/completionBridge";



export function MonacoEditor() {

  const tabs = useEditorStore((s) => s.tabs);

  const activeTab = useEditorStore((s) => s.activeTab);

  const updateContent = useEditorStore((s) => s.updateContent);

  const setSelection = useEditorStore((s) => s.setSelection);

  const settings = useSettingsStore((s) => s.settings);

  const apiStatus = useSettingsStore((s) => s.apiStatus);

  const workspace = useWorkspaceStore((s) => s.workspace);

  const tab = tabs.find((t) => t.path === activeTab);

  const controllerRef = useRef<CompletionController | null>(null);

  const disposablesRef = useRef<Array<{ dispose: () => void }>>([]);



  useEffect(() => {

    if (apiStatus === "connected") {

      useCompletionStore.getState().setStatus("ready");

    } else if (apiStatus === "disconnected") {

      useCompletionStore.getState().setStatus("offline");

    }

  }, [apiStatus]);



  useEffect(() => {
    controllerRef.current?.invalidate("workspace");
  }, [workspace?.workspaceId]);

  useEffect(() => {

    return () => {

      disposablesRef.current.forEach((d) => d.dispose());

      disposablesRef.current = [];

      controllerRef.current?.dispose();

      controllerRef.current = null;
      setActiveCompletionController(null);

    };

  }, []);



  if (!tab) {

    return (

      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-secondary)" }}>

        No file selected

      </div>

    );

  }



  const readCompletionSettings = (): CompletionSettings => {
    const currentSettings = useSettingsStore.getState().settings;
    const currentWorkspace = useWorkspaceStore.getState().workspace;
    return {
      apiUrl: currentSettings?.apiUrl ?? "http://127.0.0.1:8000",
      indexerUrl: currentSettings?.indexerUrl ?? "http://127.0.0.1:8002",
      indexerWorkspaceId: currentWorkspace?.indexerWorkspaceId ?? null,
      enabled: currentSettings?.inlineCompletionEnabled ?? true,
      model: currentSettings?.completionModel ?? currentSettings?.defaultModel ?? "default",
      debounceMs: currentSettings?.completionDebounceMs ?? 250,
      maxTokens: currentSettings?.completionMaxTokens ?? 256,
      contextLines: currentSettings?.completionContextLines ?? 50,
      repositoryContextEnabled: currentSettings?.completionRepositoryContextEnabled ?? true,
      maxRequestsPerMinute: currentSettings?.completionMaxRequestsPerMinute ?? 60,
      timeoutMs: currentSettings?.completionTimeoutMs ?? 5000,
      triggerOnTyping: currentSettings?.completionTriggerOnTyping ?? true,
    };
  };

  const handleMount = (editor: import("monaco-editor").editor.IStandaloneCodeEditor, monaco: Monaco) => {
    (window as Window & { __monacoActiveEditor__?: typeof editor }).__monacoActiveEditor__ = editor;

    disposablesRef.current.forEach((d) => d.dispose());

    disposablesRef.current = [];

    controllerRef.current?.dispose();

    const controller = new CompletionController(() => readCompletionSettings());

    controllerRef.current = controller;
    setActiveCompletionController(controller);



    disposablesRef.current.push(

      registerInlineCompletionProvider(

        monaco,

        controller,

        tab.path,

        tab.language,

        workspace?.workspaceId,

      ),

    );

    const getCompletionOptions = () => {
      const currentSettings = useSettingsStore.getState().settings;
      return {
        enabled: currentSettings?.inlineCompletionEnabled ?? true,
        triggerOnTyping: currentSettings?.completionTriggerOnTyping ?? true,
        debounceMs: currentSettings?.completionDebounceMs ?? 250,
      };
    };

    const cleanup = setupCompletionListeners(
      editor,
      controller,
      tab.path,
      getCompletionOptions,
    );

    disposablesRef.current.push({ dispose: cleanup });

    editor.addAction({
      id: "ai.triggerCompletion",
      label: "Trigger AI Completion",
      keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Space],
      run: (ed) => {
        ed.trigger("ai-completion", "editor.action.inlineSuggest.trigger", {});
      },
    });



    editor.onDidChangeCursorSelection(() => {

      const sel = editor.getSelection();

      const model = editor.getModel();

      if (!sel || !model) return;

      const text = model.getValueInRange(sel);

      if (text) {

        setSelection({

          start: model.getOffsetAt(sel.getStartPosition()),

          end: model.getOffsetAt(sel.getEndPosition()),

          text,

        });

      }

    });

  };



  return (

    <Editor

      key={tab.path}

      height="100%"

      language={tab.language}

      value={tab.content}

      theme={settings?.theme === "light" ? "light" : "vs-dark"}

      options={{

        fontSize: settings?.fontSize ?? 14,

        wordWrap: settings?.wordWrap ? "on" : "off",

        minimap: { enabled: settings?.minimap ?? true },

        lineNumbers: "on",

        scrollBeyondLastLine: false,

        automaticLayout: true,

        inlineSuggest: { enabled: settings?.inlineCompletionEnabled ?? true },

      }}

      onChange={(value) => updateContent(tab.path, value ?? "")}

      onMount={handleMount}

    />

  );

}


