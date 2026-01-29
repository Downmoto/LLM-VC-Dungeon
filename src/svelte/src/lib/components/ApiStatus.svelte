<script lang="ts">
  import { onMount } from 'svelte';
  import { apiClient, type HealthResponse } from '$lib/api/client';

  let health = $state<HealthResponse | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);

  async function checkHealth() {
    loading = true;
    error = null;
    try {
      health = await apiClient.healthCheck();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to connect to API';
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    checkHealth();
  });
</script>

<div class="api-status">
  <h3>API Status</h3>
  
  {#if loading}
    <p class="loading">Checking API connection...</p>
  {:else if error}
    <div class="error">
      <p>❌ {error}</p>
      <button onclick={checkHealth}>Retry</button>
    </div>
  {:else if health}
    <div class="success">
      <p>✅ Status: <strong>{health.status}</strong></p>
      <p>🤖 AI Stack Mode: <strong>{health.ai_stack_mode}</strong></p>
      <p>🔌 Provider Initialized: <strong>{health.provider_initialized ? 'Yes' : 'No'}</strong></p>
      <button onclick={checkHealth}>Refresh</button>
    </div>
  {/if}
</div>

<style>
  .api-status {
    padding: 1.5rem;
    border: 2px solid #333;
    border-radius: 8px;
    margin-bottom: 2rem;
    background: #f8f8f8;
  }

  h3 {
    margin-top: 0;
    color: #333;
  }

  .loading {
    color: #666;
    font-style: italic;
  }

  .error {
    color: #c00;
  }

  .success {
    color: #060;
  }

  .success p {
    margin: 0.5rem 0;
  }

  button {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
  }

  button:hover {
    background: #0056b3;
  }

  strong {
    font-weight: 600;
  }
</style>
