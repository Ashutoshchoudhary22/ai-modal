import { describe, expect, it, beforeEach } from "vitest";
import { useEditorStore } from "../src/renderer/src/state/editorStore";

describe("editorStore", () => {
  beforeEach(() => {
    useEditorStore.setState({
      tabs: [],
      activeTab: null,
      selection: null,
      proposedChanges: [],
      reviewIndex: 0,
    });
  });

  it("opens and tracks dirty state", () => {
    useEditorStore.getState().openTab("src/a.ts", "hello");
    expect(useEditorStore.getState().tabs).toHaveLength(1);
    expect(useEditorStore.getState().activeTab).toBe("src/a.ts");

    useEditorStore.getState().updateContent("src/a.ts", "hello world");
    expect(useEditorStore.getState().tabs[0].dirty).toBe(true);
  });

  it("manages proposed changes for diff review", () => {
    useEditorStore.getState().addProposedChange({
      path: "src/a.ts",
      original: "old",
      modified: "new",
      source: "agent",
    });
    expect(useEditorStore.getState().proposedChanges).toHaveLength(1);

    const accepted = useEditorStore.getState().acceptChange(0);
    expect(accepted?.modified).toBe("new");
    expect(useEditorStore.getState().proposedChanges).toHaveLength(0);
  });
});
