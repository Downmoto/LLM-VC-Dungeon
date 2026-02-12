// command system for handling special commands in the game

import type { MessageLogger } from './messageLogger.svelte';

export interface CommandContext {
  logger: MessageLogger;
  args: string[];
  rawInput: string;
}

export type CommandHandler = (ctx: CommandContext) => void | Promise<void>;

export interface Command {
  name: string;
  aliases?: string[];
  description: string;
  handler: CommandHandler;
}

/**
 * creates a command registry that can register and execute commands
 */
export function createCommandRegistry() {
  const commands = new Map<string, Command>();

  return {
    /**
     * registers a new command
     */
    register(command: Command) {
      commands.set(command.name, command);
      // register aliases
      if (command.aliases) {
        for (const alias of command.aliases) {
          commands.set(alias, command);
        }
      }
    },

    /**
     * checks if input is a command (starts with /)
     */
    isCommand(input: string): boolean {
      return input.trim().startsWith('/');
    },

    /**
     * parses and executes a command
     * @returns true if command was found and executed, false otherwise
     */
    async execute(input: string, logger: MessageLogger): Promise<boolean> {
      const trimmed = input.trim();
      
      // check if it's a command
      if (!this.isCommand(trimmed)) {
        return false;
      }

      // parse command and args
      const parts = trimmed.slice(1).split(/\s+/);
      const commandName = parts[0].toLowerCase();
      const args = parts.slice(1);

      // find command
      const command = commands.get(commandName);
      if (!command) {
        logger.addError(`unknown command: /${commandName}`);
        logger.addSystem('type /help for available commands');
        return true;
      }

      // execute command
      try {
        await command.handler({
          logger,
          args,
          rawInput: trimmed
        });
      } catch (err) {
        logger.addError(`command failed: ${err instanceof Error ? err.message : 'unknown error'}`);
      }

      return true;
    },

    /**
     * gets all registered commands
     */
    getAll(): Command[] {
      const uniqueCommands = new Map<string, Command>();
      for (const [name, command] of commands) {
        if (command.name === name) {
          uniqueCommands.set(name, command);
        }
      }
      return Array.from(uniqueCommands.values());
    },

    /**
     * gets a specific command by name
     */
    get(name: string): Command | undefined {
      return commands.get(name.toLowerCase());
    }
  };
}

export type CommandRegistry = ReturnType<typeof createCommandRegistry>;
