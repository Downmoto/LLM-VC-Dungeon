<script lang="ts">
  import { apiClient, ApiError } from '$lib/api/client';
  import { onMount, onDestroy } from 'svelte';
  import Terminal from '$lib/components/Terminal.svelte';
  import { createMessageLogger } from '$lib/utils/messageLogger.svelte';
  import { createCommandRegistry } from '$lib/utils/commandSystem';

  // game state
  let userInput = $state('');
  let loading = $state(false);
  let connected = $state(false);

  // message logger
  const logger = createMessageLogger();

  // command registry
  const commands = createCommandRegistry();

  // register game commands
  commands.register({
    name: 'help',
    aliases: ['h', '?'],
    description: 'show available commands',
    handler: ({ logger }) => {
      logger.addSystem('');
      logger.addSystem('available commands:');
      logger.addSystem('  /help      - show this message');
      logger.addSystem('  /clear     - clear the terminal');
      logger.addSystem('  /status    - check connection status');
      logger.addSystem('  /new-game  - start a new game');
      logger.addSystem('  /load-game - load a saved game');
      logger.addSystem('');
      logger.addSystem('or type any action to interact with the dungeon:');
      logger.addSystem('  "look around"');
      logger.addSystem('  "go north"');
      logger.addSystem('  "pick up sword"');
      logger.addSystem('  "attack goblin"');
      logger.addSystem('');
    }
  });

  commands.register({
    name: 'clear',
    aliases: ['cls'],
    description: 'clear the terminal',
    handler: ({ logger }) => {
      logger.clear();
      logger.addSystem('terminal cleared.');
    }
  });

  commands.register({
    name: 'status',
    description: 'check connection status',
    handler: ({ logger }) => {
      if (connected) {
        logger.addSuccess('connected to dungeon master');
      } else {
        logger.addError('disconnected from server');
      }
    }
  });

  commands.register({
    name: 'new-game',
    aliases: ['new', 'restart'],
    description: 'start a new game',
    handler: ({ logger }) => {
      logger.addSystem('');
      logger.addSystem('starting new game...');
      logger.addSystem('(not yet implemented)');
      logger.addSystem('');
    }
  });

  commands.register({
    name: 'load-game',
    aliases: ['load'],
    description: 'load a saved game',
    handler: ({ logger }) => {
      logger.addSystem('');
      logger.addSystem('loading saved game...');
      logger.addSystem('(not yet implemented)');
      logger.addSystem('');
    }
  });

  // check api connection on mount
  let pollInterval: ReturnType<typeof setInterval>;

  async function checkConnection() {
    try {
      await apiClient.healthCheck();
      connected = true;
    } catch (err) {
      connected = false;
    }
  }

  onMount(async () => {
    logger.addSystem('initializing connection to dungeon master...');
    try {
      const health = await apiClient.healthCheck();
      connected = true;
      logger.addSystem(`connected. model: ${health.ollama_model}`);
      logger.addSystem('');
      logger.addSystem('========================================');
      logger.addSystem('   llm voice-controlled dungeon v1.0');
      logger.addSystem('========================================');
      logger.addSystem('');
      logger.addSystem('you stand at the entrance of a dark dungeon.');
      logger.addSystem('type your actions and press enter.');
      logger.addSystem('type /help for available commands.');
      logger.addSystem('');
    } catch (err) {
      connected = false;
      logger.addError('failed to connect to server');
      logger.addSystem('check /api-check for diagnostics');
    }

    // poll connection status every 5 seconds
    pollInterval = setInterval(checkConnection, 5000);
  });

  onDestroy(() => {
    if (pollInterval) {
      clearInterval(pollInterval);
    }
  });

  async function handleSubmit(input: string) {
    const trimmed = input.trim();
    if (!trimmed) return;

    userInput = '';
    logger.addInput(trimmed);

    // check if it's a command
    if (commands.isCommand(trimmed)) {
      await commands.execute(trimmed, logger);
      return;
    }

    // send to api
    loading = true;

    try {
      const response = await apiClient.processGameTurn({ user_input: trimmed });
      logger.addOutput('');
      // split narrative into lines for better display
      const lines = response.narrative.split('\n');
      for (const line of lines) {
        logger.addOutput(line);
      }
      logger.addOutput('');
    } catch (err) {
      if (err instanceof ApiError) {
        logger.addError(err.detail);
      } else {
        logger.addError(err instanceof Error ? err.message : 'unknown error');
      }
    } finally {
      loading = false;
    }
  }
</script>

<Terminal
  title="dungeon.exe"
  messages={logger.messages}
  {connected}
  {loading}
  bind:userInput
  onSubmit={handleSubmit}
  linkHref="/api-check"
  linkText="api"
/>
