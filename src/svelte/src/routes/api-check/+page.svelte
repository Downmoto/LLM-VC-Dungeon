<script lang="ts">
  import { onMount } from 'svelte';
  import { apiClient, type HealthResponse } from '$lib/api/client';
  import Terminal from '$lib/components/Terminal.svelte';
  import { createMessageLogger } from '$lib/utils/messageLogger.svelte';

  let health = $state<HealthResponse | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);

  // message logger
  const logger = createMessageLogger();

  async function checkHealth() {
    loading = true;
    error = null;
    logger.addSystem('running diagnostics...');
    
    try {
      health = await apiClient.healthCheck();
      logger.addSuccess(`status: ${health.status}`);
      logger.addSuccess(`ollama url: ${health.ollama_url}`);
      logger.addSuccess(`model: ${health.ollama_model}`);
      logger.addSuccess(`endpoints: ${Object.values(health.endpoints).join(', ')}`);
      logger.addSystem('all systems operational');
    } catch (err) {
      error = err instanceof Error ? err.message : 'failed to connect to api';
      logger.addError(`connection failed: ${error}`);
    } finally {
      loading = false;
    }
  }

  function clearLogs() {
    logger.clear();
    health = null;
    error = null;
  }

  onMount(() => {
    logger.addSystem('========================================');
    logger.addSystem('         api diagnostics v1.0');
    logger.addSystem('========================================');
    logger.addSystem('');
    checkHealth();
  });
</script>

<Terminal
  title="diagnostics.exe"
  messages={logger.messages}
  connected={!!(health && !error)}
  {loading}
  showInput={false}
  linkHref="/"
  linkText="game"
>
  {#snippet footerContent()}
  <div>
    <div class="button-row">
      <button onclick={checkHealth} disabled={loading} class="terminal-btn">
        [refresh]
      </button>
      <button onclick={clearLogs} disabled={loading} class="terminal-btn">
        [clear]
      </button>
    </div>

    <div class="info-section">
      <div class="terminal-line system">
        <span class="system-text">----------------------------------------</span>
      </div>
      <div class="terminal-line system">
        <span class="system-text">server endpoints:</span>
      </div>
      <div class="terminal-line">
        <span class="dim-text">  backend:  http://localhost:8000</span>
      </div>
      <div class="terminal-line">
        <span class="dim-text">  frontend: http://localhost:5173</span>
      </div>
    </div>
  </div>
  {/snippet}
</Terminal>

<style>
  .button-row {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .terminal-btn {
    background: transparent;
    border: 1px solid #444;
    color: #888;
    padding: 0.5rem 1rem;
    font-family: inherit;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .terminal-btn:hover:not(:disabled) {
    border-color: #888;
    color: #fff;
  }

  .terminal-btn:disabled {
    color: #444;
    border-color: #333;
    cursor: not-allowed;
  }

  .info-section {
    margin-top: 1rem;
  }

  .terminal-line {
    min-height: 1.5em;
  }

  .system-text {
    color: #888;
  }

  .dim-text {
    color: #666;
  }
</style>
