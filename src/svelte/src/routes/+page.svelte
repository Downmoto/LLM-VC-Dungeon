<script lang="ts">
  import { apiClient, ApiError } from '$lib/api/client';
  import type { GameMapResponse } from '$lib/api/client';
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
      logger.addSystem('  /map       - show discovered dungeon map');
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
    handler: async ({ logger }) => {
      if (loading) {
        logger.addSystem('already processing a request, please wait.');
        return;
      }

      loading = true;
      logger.addSystem('');
      logger.addSystem('starting new game...');

      try {
        const response = await apiClient.newGame();
        logger.addSuccess(response.message);
        logger.addSystem('');
        const lines = response.initial_room.split('\n');
        for (const line of lines) {
          logger.addOutput(line);
        }
        logger.addSystem('');
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

  function renderMapLines(mapData: GameMapResponse): string[] {
    const roomById = new Map(mapData.rooms.map((room) => [room.id, room]));
    const coords = new Map<string, { x: number; y: number }>();
    const occupied = new Map<string, string>();
    const queue: string[] = [];
    const deltas: Record<string, { x: number; y: number }> = {
      north: { x: 0, y: 1 },
      south: { x: 0, y: -1 },
      east: { x: 1, y: 0 },
      west: { x: -1, y: 0 }
    };

    const current = mapData.current_room_id;
    coords.set(current, { x: 0, y: 0 });
    occupied.set('0,0', current);
    queue.push(current);

    while (queue.length > 0) {
      const roomId = queue.shift();
      if (!roomId) continue;
      const room = roomById.get(roomId);
      const pos = coords.get(roomId);
      if (!room || !pos) continue;

      for (const [direction, neighborId] of Object.entries(room.exits)) {
        if (coords.has(neighborId)) continue;
        const delta = deltas[direction.toLowerCase()];
        if (!delta) continue;

        let nx = pos.x + delta.x;
        let ny = pos.y + delta.y;
        while (occupied.has(`${nx},${ny}`)) {
          nx += delta.x;
          ny += delta.y;
        }

        coords.set(neighborId, { x: nx, y: ny });
        occupied.set(`${nx},${ny}`, neighborId);
        queue.push(neighborId);
      }
    }

    const unattached = mapData.rooms.filter((r) => !coords.has(r.id)).map((r) => r.id);
    let spillY = 0;
    for (const id of unattached) {
      coords.set(id, { x: 4, y: spillY });
      occupied.set(`4,${spillY}`, id);
      spillY -= 1;
    }

    const points = Array.from(coords.entries()).map(([id, pos]) => ({ id, ...pos }));
    const minX = Math.min(...points.map((p) => p.x));
    const maxX = Math.max(...points.map((p) => p.x));
    const minY = Math.min(...points.map((p) => p.y));
    const maxY = Math.max(...points.map((p) => p.y));
    const roomAt = new Map(points.map((p) => [`${p.x},${p.y}`, p.id]));
    const width = 12;

    const lines: string[] = [];
    lines.push(`theme: ${mapData.theme}`);
    lines.push(`current room: ${current}`);
    lines.push('');

    for (let y = maxY; y >= minY; y -= 1) {
      const row: string[] = [];
      for (let x = minX; x <= maxX; x += 1) {
        const id = roomAt.get(`${x},${y}`);
        if (!id) {
          row.push(' '.repeat(width));
          continue;
        }
        const marker = id === current ? '*' : ' ';
        const label = `[${id}${marker}]`;
        row.push(label.padEnd(width));
      }
      lines.push(row.join(''));
    }

    lines.push('');
    lines.push('legend: [room_id*] = current room');
    return lines;
  }

  commands.register({
    name: 'map',
    aliases: ['m'],
    description: 'show dungeon room map',
    handler: async ({ logger }) => {
      if (loading) {
        logger.addSystem('already processing a request, please wait.');
        return;
      }

      loading = true;
      logger.addSystem('');
      logger.addSystem('fetching dungeon map...');
      try {
        const mapData = await apiClient.getGameMap();
        const lines = renderMapLines(mapData);
        for (const line of lines) {
          logger.addOutput(line);
        }
        logger.addSystem('');
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
    if (loading) {
      return;
    }

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
