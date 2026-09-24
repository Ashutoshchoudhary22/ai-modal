export interface Command {
  id: string;
  title: string;
  shortcut?: string;
  handler: () => void | Promise<void>;
}

class CommandRegistry {
  private commands = new Map<string, Command>();

  register(command: Command): void {
    this.commands.set(command.id, command);
  }

  execute(id: string): void {
    const cmd = this.commands.get(id);
    if (cmd) void cmd.handler();
  }

  list(): Command[] {
    return Array.from(this.commands.values());
  }
}

export const commandRegistry = new CommandRegistry();
