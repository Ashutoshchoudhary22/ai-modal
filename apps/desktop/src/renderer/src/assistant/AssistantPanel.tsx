import { useState } from "react";
import { useAssistantStore } from "../state/assistantStore";
import { useSettingsStore } from "../state/settingsStore";
import { useWorkspaceStore } from "../state/workspaceStore";
import { useEditorStore } from "../state/editorStore";
import { useAgentStore } from "../state/agentStore";
import { useNotificationStore } from "../state/notificationStore";
import { streamChat } from "../api/client";
import { streamAgentRun } from "../api/agent";
import { MarkdownMessage } from "./MarkdownMessage";
import { InlineCompletionSettings } from "../settings/InlineCompletionSettings";

type AssistantMode = "chat" | "agent" | "completion";

export function AssistantPanel() {
  const [input, setInput] = useState("");
  const messages = useAssistantStore((s) => s.messages);
  const attachments = useAssistantStore((s) => s.attachments);
  const mode = useAssistantStore((s) => s.mode) as AssistantMode;
  const streaming = useAssistantStore((s) => s.streaming);
  const { settings, apiStatus, provider, modelId } = useSettingsStore();
  const workspace = useWorkspaceStore((s) => s.workspace);
  const activeTab = useEditorStore((s) => s.activeTab);
  const tabs = useEditorStore((s) => s.tabs);
  const addAttachment = useAssistantStore((s) => s.addAttachment);
  const setMode = useAssistantStore((s) => s.setMode);
  const addEvent = useAgentStore((s) => s.addEvent);
  const setRunning = useAgentStore((s) => s.setRunning);
  const notify = useNotificationStore((s) => s.notify);

  const attachCurrentFile = () => {
    const tab = tabs.find((t) => t.path === activeTab);
    if (!tab) return;
    addAttachment({ type: "file", label: tab.path, content: tab.content });
  };

  const sendMessage = async () => {
    if (!input.trim() || !settings) return;
    if (apiStatus !== "connected") {
      notify("error", "AI service unavailable");
      return;
    }

    const userContent = input;
    setInput("");
    const addMessage = useAssistantStore.getState().addMessage;
    const updateMessage = useAssistantStore.getState().updateMessage;
    addMessage({ role: "user", content: userContent });

    if (mode === "agent") {
      if (!workspace) {
        notify("error", "Open a workspace first");
        return;
      }
      setRunning(true);
      addEvent({ type: "status", message: "Agent started" });
      const controller = new AbortController();
      useAssistantStore.getState().setAbortController(controller);
      try {
        await streamAgentRun(
          settings.agentUrl,
          {
            workspace_id: workspace.workspaceId,
            task: userContent,
            root_path: workspace.rootPath,
            max_iterations: settings.maxAgentIterations,
          },
          (event) => {
            addEvent({
              type: String(event.type),
              message: JSON.stringify(event).slice(0, 500),
            });
            if (event.type === "run.result") {
              const result = event.result as { final_response?: string };
              addMessage({ role: "assistant", content: result?.final_response ?? "Agent completed." });
            }
          },
          controller.signal,
        );
      } catch (err) {
        notify("error", err instanceof Error ? err.message : "Agent failed");
      } finally {
        setRunning(false);
        useAssistantStore.getState().setAbortController(null);
      }
      return;
    }

    const assistantId = addMessage({ role: "assistant", content: "", streaming: true });
    useAssistantStore.getState().setStreaming(true);
    const controller = new AbortController();
    useAssistantStore.getState().setAbortController(controller);

    const contextParts = attachments.map((a) => `[${a.type}: ${a.label}]\n${a.content}`);
    const chatMessages = [
      ...messages.map((m) => ({ role: m.role as "user" | "assistant", content: m.content })),
      {
        role: "user" as const,
        content: contextParts.length
          ? `${contextParts.join("\n\n")}\n\n${userContent}`
          : userContent,
      },
    ];

    try {
      let full = "";
      await streamChat(
        settings.apiUrl,
        chatMessages,
        { maxTokens: 2048, temperature: 0.2, model: settings.defaultModel },
        (chunk) => {
          full += chunk;
          updateMessage(assistantId, full, true);
        },
        controller.signal,
      );
      updateMessage(assistantId, full, false);
    } catch (err) {
      updateMessage(assistantId, `Error: ${err instanceof Error ? err.message : "Failed"}`, false);
    } finally {
      useAssistantStore.getState().setStreaming(false);
      useAssistantStore.getState().setAbortController(null);
    }
  };

  const cancel = () => {
    useAssistantStore.getState().abortController?.abort();
    useAssistantStore.getState().setStreaming(false);
    setRunning(false);
  };

  return (
    <div className="panel" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div className="panel-header" style={{ display: "flex", justifyContent: "space-between" }}>
        <span>AI Assistant</span>
        <div style={{ display: "flex", gap: 4 }}>
          <button onClick={() => setMode("chat")} style={{ opacity: mode === "chat" ? 1 : 0.5 }}>Chat</button>
          <button onClick={() => setMode("agent")} style={{ opacity: mode === "agent" ? 1 : 0.5 }}>Agent</button>
          <button onClick={() => setMode("completion")} style={{ opacity: mode === "completion" ? 1 : 0.5 }}>Completion</button>
        </div>
      </div>
      {mode === "completion" ? (
        <InlineCompletionSettings />
      ) : (
        <>
      <div style={{ padding: "4px 8px", fontSize: 11, color: "var(--text-secondary)", borderBottom: "1px solid var(--border)" }}>
        Model: {modelId ?? settings?.defaultModel ?? "default"} | Provider: {provider ?? "—"}
        {attachments.length > 0 && ` | Context: ${attachments.length} attachment(s)`}
      </div>
      <div style={{ flex: 1, overflow: "auto", padding: 8 }}>
        {messages.length === 0 && (
          <div style={{ color: "var(--text-secondary)", textAlign: "center", marginTop: 32 }}>
            {apiStatus === "connected" ? "Ask AI anything..." : "AI service unavailable"}
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 4 }}>
              {msg.role === "user" ? "You" : "Assistant"}
            </div>
            <MarkdownMessage content={msg.content} />
          </div>
        ))}
      </div>
      <div style={{ padding: 8, borderTop: "1px solid var(--border)" }}>
        <div style={{ display: "flex", gap: 4, marginBottom: 4 }}>
          <button onClick={attachCurrentFile} disabled={!activeTab}>Attach File</button>
          <button onClick={() => useAssistantStore.getState().clearMessages()}>Clear</button>
          {streaming && <button onClick={cancel}>Cancel</button>}
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void sendMessage();
              }
            }}
            placeholder={mode === "agent" ? "Describe agent task..." : "Ask AI..."}
            style={{ flex: 1, minHeight: 60, resize: "none" }}
          />
          <button className="primary" onClick={() => void sendMessage()} disabled={streaming}>
            Send
          </button>
        </div>
      </div>
        </>
      )}
    </div>
  );
}
