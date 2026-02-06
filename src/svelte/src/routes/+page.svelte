<script lang="ts">
  import { apiClient, ApiError, type GameTurnResponse } from '$lib/api/client';
  import { onMount } from 'svelte';

  // game state
  let userInput = $state('');
  let loading = $state(false);
  let error = $state<string | null>(null);
  let history = $state<Array<{ type: 'input' | 'output' | 'system'; text: string }>>([]);
  let terminalRef = $state<HTMLDivElement | null>(null);
  let inputRef = $state<HTMLInputElement | null>(null);
  let connected = $state(false);

  // scroll to bottom when history changes
  $effect(() => {
    if (history.length && terminalRef) {
      terminalRef.scrollTop = terminalRef.scrollHeight;
    }
  });

  // check api connection on mount
  onMount(async () => {
    addSystemMessage('initializing connection to dungeon master...');
    try {
      const health = await apiClient.healthCheck();
      connected = true;
      addSystemMessage(`connected. model: ${health.ollama_model}`);
      addSystemMessage('');
      addSystemMessage('========================================');
      addSystemMessage('   llm voice-controlled dungeon v1.0');
      addSystemMessage('========================================');
      addSystemMessage('');
      addSystemMessage('you stand at the entrance of a dark dungeon.');
      addSystemMessage('type your actions and press enter.');
      addSystemMessage('type "help" for available commands.');
      addSystemMessage('');
    } catch (err) {
      addSystemMessage('error: failed to connect to server');
      addSystemMessage('check /api-check for diagnostics');
    }
    inputRef?.focus();
  });

  function addSystemMessage(text: string) {
    history = [...history, { type: 'system', text }];
  }

  function addInputMessage(text: string) {
    history = [...history, { type: 'input', text: `> ${text}` }];
  }

  function addOutputMessage(text: string) {
    history = [...history, { type: 'output', text }];
  }

  async function handleSubmit() {
    const input = userInput.trim();
    if (!input) return;

    userInput = '';
    addInputMessage(input);

    // handle local commands
    if (input.toLowerCase() === 'help') {
      addSystemMessage('');
      addSystemMessage('available commands:');
      addSystemMessage('  help     - show this message');
      addSystemMessage('  clear    - clear the terminal');
      addSystemMessage('  status   - check connection status');
      addSystemMessage('');
      addSystemMessage('or type any action to interact with the dungeon:');
      addSystemMessage('  "look around"');
      addSystemMessage('  "go north"');
      addSystemMessage('  "pick up sword"');
      addSystemMessage('  "attack goblin"');
      addSystemMessage('');
      return;
    }

    if (input.toLowerCase() === 'clear') {
      history = [];
      addSystemMessage('terminal cleared.');
      return;
    }

    if (input.toLowerCase() === 'status') {
      if (connected) {
        addSystemMessage('status: connected to dungeon master');
      } else {
        addSystemMessage('status: disconnected');
      }
      return;
    }

    // send to api
    loading = true;
    error = null;

    try {
      const response = await apiClient.processGameTurn({ user_input: input });
      addOutputMessage('');
      // split narrative into lines for better display
      const lines = response.narrative.split('\n');
      for (const line of lines) {
        addOutputMessage(line);
      }
      addOutputMessage('');
    } catch (err) {
      if (err instanceof ApiError) {
        addSystemMessage(`error: ${err.detail}`);
      } else {
        addSystemMessage(`error: ${err instanceof Error ? err.message : 'unknown error'}`);
      }
    } finally {
      loading = false;
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      handleSubmit();
    }
  }

  function focusInput() {
    inputRef?.focus();
  }
</script>

<div class="terminal-container" onclick={focusInput} role="presentation">
  <div class="terminal-header">
    <span class="terminal-title">dungeon.exe</span>
    <a href="/api-check" class="terminal-link">[api]</a>
  </div>
  
  <div class="terminal-body" bind:this={terminalRef}>
    {#each history as line}
      <div class="terminal-line {line.type}">
        {#if line.type === 'system'}
          <span class="system-text">{line.text}</span>
        {:else if line.type === 'input'}
          <span class="input-text">{line.text}</span>
        {:else}
          <span class="output-text">{line.text}</span>
        {/if}
      </div>
    {/each}
    
    <div class="input-line">
      <span class="prompt">&gt;</span>
      <input
        type="text"
        bind:value={userInput}
        bind:this={inputRef}
        onkeydown={handleKeydown}
        disabled={loading}
        placeholder={loading ? 'processing...' : ''}
        class="terminal-input"
        autocomplete="off"
        spellcheck="false"
      />
      {#if loading}
        <span class="cursor blink">_</span>
      {/if}
    </div>
  </div>
  
  <div class="terminal-footer">
    <span class="status-indicator" class:connected></span>
    <span class="status-text">{connected ? 'connected' : 'disconnected'}</span>
  </div>
</div>

<style>
  :global(*) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    padding: 0;
    background: #000 !important;
    min-height: 100vh;
    font-family: 'Courier New', 'Monaco', 'Consolas', monospace;
  }

  .terminal-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 900px;
    margin: 0 auto;
    background: #0a0a0a;
    border-left: 1px solid #333;
    border-right: 1px solid #333;
  }

  .terminal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 1rem;
    background: #1a1a1a;
    border-bottom: 1px solid #333;
  }

  .terminal-title {
    color: #888;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .terminal-link {
    color: #666;
    text-decoration: none;
    font-size: 0.8rem;
    background: transparent;
  }

  .terminal-link:hover {
    color: #fff;
    background: transparent;
  }

  .terminal-body {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    font-size: 1rem;
    line-height: 1.5;
  }

  .terminal-line {
    white-space: pre-wrap;
    word-wrap: break-word;
    min-height: 1.5em;
  }

  .system-text {
    color: #888;
  }

  .input-text {
    color: #fff;
    font-weight: bold;
  }

  .output-text {
    color: #ccc;
  }

  .input-line {
    display: flex;
    align-items: center;
    margin-top: 0.5rem;
  }

  .prompt {
    color: #fff;
    margin-right: 0.5rem;
    font-weight: bold;
  }

  .terminal-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: #fff;
    font-family: inherit;
    font-size: inherit;
    padding: 0;
    caret-color: #fff;
  }

  .terminal-input::placeholder {
    color: #444;
  }

  .terminal-input:disabled {
    color: #666;
  }

  .cursor {
    color: #fff;
    font-weight: bold;
  }

  .cursor.blink {
    animation: blink 1s step-end infinite;
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }

  .terminal-footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: #1a1a1a;
    border-top: 1px solid #333;
  }

  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #444;
  }

  .status-indicator.connected {
    background: #888;
    box-shadow: 0 0 4px #888;
  }

  .status-text {
    color: #666;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  /* scrollbar styling */
  .terminal-body::-webkit-scrollbar {
    width: 8px;
  }

  .terminal-body::-webkit-scrollbar-track {
    background: #0a0a0a;
  }

  .terminal-body::-webkit-scrollbar-thumb {
    background: #333;
    border-radius: 4px;
  }

  .terminal-body::-webkit-scrollbar-thumb:hover {
    background: #444;
  }

  /* scanline effect */
  .terminal-container::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: repeating-linear-gradient(
      0deg,
      rgba(0, 0, 0, 0.15),
      rgba(0, 0, 0, 0.15) 1px,
      transparent 1px,
      transparent 2px
    );
    pointer-events: none;
    z-index: 1000;
  }

  /* crt glow effect */
  .terminal-body {
    text-shadow: 0 0 2px rgba(255, 255, 255, 0.1);
  }
</style>
