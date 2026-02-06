<script lang="ts">
  import { onMount } from 'svelte';
  import { apiClient, type HealthResponse } from '$lib/api/client';

  let health = $state<HealthResponse | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let logs = $state<Array<{ type: 'system' | 'success' | 'error'; text: string }>>([]);

  function addLog(type: 'system' | 'success' | 'error', text: string) {
    logs = [...logs, { type, text }];
  }

  async function checkHealth() {
    loading = true;
    error = null;
    addLog('system', 'running diagnostics...');
    
    try {
      health = await apiClient.healthCheck();
      addLog('success', `status: ${health.status}`);
      addLog('success', `ollama url: ${health.ollama_url}`);
      addLog('success', `model: ${health.ollama_model}`);
      addLog('success', `endpoints: ${Object.values(health.endpoints).join(', ')}`);
      addLog('system', 'all systems operational');
    } catch (err) {
      error = err instanceof Error ? err.message : 'failed to connect to api';
      addLog('error', `connection failed: ${error}`);
    } finally {
      loading = false;
    }
  }

  function clearLogs() {
    logs = [];
    health = null;
    error = null;
  }

  onMount(() => {
    addLog('system', '========================================');
    addLog('system', '         api diagnostics v1.0');
    addLog('system', '========================================');
    addLog('system', '');
    checkHealth();
  });
</script>

<div class="terminal-container">
  <div class="terminal-header">
    <span class="terminal-title">diagnostics.exe</span>
    <a href="/" class="terminal-link">[game]</a>
  </div>
  
  <div class="terminal-body">
    {#each logs as log}
      <div class="terminal-line {log.type}">
        {#if log.type === 'system'}
          <span class="system-text">{log.text}</span>
        {:else if log.type === 'success'}
          <span class="success-text">[ok] {log.text}</span>
        {:else}
          <span class="error-text">[err] {log.text}</span>
        {/if}
      </div>
    {/each}
    
    {#if loading}
      <div class="terminal-line">
        <span class="system-text">checking connection<span class="blink">_</span></span>
      </div>
    {/if}

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
  
  <div class="terminal-footer">
    <span class="status-indicator" class:connected={health && !error}></span>
    <span class="status-text">{health && !error ? 'connected' : 'disconnected'}</span>
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

  .success-text {
    color: #aaa;
  }

  .error-text {
    color: #fff;
    font-weight: bold;
  }

  .dim-text {
    color: #666;
  }

  .blink {
    animation: blink 1s step-end infinite;
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }

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
