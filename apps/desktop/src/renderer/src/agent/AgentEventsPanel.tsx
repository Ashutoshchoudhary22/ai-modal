import { useAgentStore } from "../state/agentStore";
import { useAssistantStore } from "../state/assistantStore";

export function AgentEventsPanel() {
  const events = useAgentStore((s) => s.events);
  const running = useAgentStore((s) => s.running);
  const pendingApproval = useAgentStore((s) => s.pendingApproval);

  const stopAgent = () => {
    useAssistantStore.getState().abortController?.abort();
    useAgentStore.getState().setRunning(false);
    useAgentStore.getState().addEvent({ type: "status", message: "Agent cancelled by user" });
  };

  return (
    <div style={{ padding: 8, height: "100%", overflow: "auto", fontSize: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
        <span>Agent Events {running && "(running)"}</span>
        {running && <button onClick={stopAgent}>Stop Agent</button>}
      </div>
      {pendingApproval && (
        <div style={{ padding: 8, background: "var(--bg-tertiary)", marginBottom: 8, borderRadius: 4 }}>
          <div>Agent wants to: {pendingApproval.tool}</div>
          <pre style={{ fontSize: 10, margin: "4px 0" }}>{JSON.stringify(pendingApproval.args, null, 2)}</pre>
          <button onClick={() => useAgentStore.getState().setPendingApproval(null)}>Dismiss</button>
        </div>
      )}
      {events.length === 0 && <div style={{ color: "var(--text-secondary)" }}>No agent events</div>}
      {events.map((evt) => (
        <div key={evt.id} style={{ padding: "4px 0", borderBottom: "1px solid var(--border)" }}>
          <span style={{ color: "var(--accent)" }}>[{evt.type}]</span> {evt.message.slice(0, 200)}
        </div>
      ))}
    </div>
  );
}
