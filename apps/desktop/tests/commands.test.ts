import { describe, expect, it } from "vitest";
import { commandRegistry } from "../src/renderer/src/state/commands";

describe("CommandRegistry", () => {
  it("registers and executes commands", () => {
    let executed = false;
    commandRegistry.register({
      id: "test-cmd",
      title: "Test Command",
      handler: () => {
        executed = true;
      },
    });
    commandRegistry.execute("test-cmd");
    expect(executed).toBe(true);
  });

  it("lists registered commands", () => {
    commandRegistry.register({ id: "list-test", title: "List Test", handler: () => {} });
    const commands = commandRegistry.list();
    expect(commands.some((c) => c.id === "list-test")).toBe(true);
  });
});
