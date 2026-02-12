<script lang="ts">
  import { apiClient, ApiError, type GameTurnResponse } from '$lib/api/client';

  let userInput = $state('');
  let narrative = $state<string | null>(null);
  let action = $state<Record<string, any> | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);
  let history = $state<Array<{ input: string; narrative: string; action?: Record<string, any> }>>([]);

  async function handleGameTurn() {
    if (!userInput.trim()) {
      error = 'please enter an action';
      return;
    }

    loading = true;
    error = null;
    narrative = null;
    action = null;

    try {
      const response = await apiClient.processGameTurn({
        user_input: userInput.trim(),
      });
      narrative = response.narrative;
      action = response.action || null;
      
      // add to history
      history = [...history, { 
        input: userInput.trim(), 
        narrative: response.narrative,
        action: response.action 
      }];
      
      // clear input
      userInput = '';
    } catch (err) {
      if (err instanceof ApiError) {
        error = `api error: ${err.detail}`;
      } else {
        error = err instanceof Error ? err.message : 'failed to process game turn';
      }
    } finally {
      loading = false;
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
      handleGameTurn();
    }
  }

  function clearHistory() {
    history = [];
    narrative = null;
    action = null;
    error = null;
  }
</script>

<div class="game-turn">
  <h3>🎮 game turn</h3>
  
  <div class="form-group">
    <label for="user-input">your action</label>
    <textarea
      id="user-input"
      bind:value={userInput}
      onkeydown={handleKeydown}
      placeholder="enter your action... (cmd/ctrl+enter to submit)"
      rows="3"
    ></textarea>
  </div>

  <div class="button-group">
    <button 
      onclick={handleGameTurn} 
      disabled={loading || !userInput.trim()}
      class="submit-btn"
    >
      {loading ? 'processing...' : 'submit action'}
    </button>
    
    {#if history.length > 0}
      <button 
        onclick={clearHistory}
        class="clear-btn"
        disabled={loading}
      >
        clear history
      </button>
    {/if}
  </div>

  {#if error}
    <div class="error-message">
      ❌ {error}
    </div>
  {/if}

  {#if narrative}
    <div class="current-narrative">
      <h4>current narrative:</h4>
      <p>{narrative}</p>
      {#if action}
        <div class="action-info">
          <strong>action detected:</strong> 
          <code>{JSON.stringify(action, null, 2)}</code>
        </div>
      {/if}
    </div>
  {/if}

  {#if history.length > 0}
    <div class="history">
      <h4>turn history:</h4>
      {#each history as turn, index}
        <div class="turn">
          <div class="turn-number">turn {index + 1}</div>
          {#if turn.action}
            <div class="turn-action">
              <strong>detected:</strong> 
              <code>{JSON.stringify(turn.action)}</code>
            </div>
          {/if}
          <div class="turn-input">
            <strong>action:</strong> {turn.input}
          </div>
          <div class="turn-narrative">
            <strong>narrative:</strong> {turn.narrative}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .game-turn {
    padding: 1.5rem;
    border: 2px solid #333;
    border-radius: 8px;
    margin-bottom: 2rem;
    background: #fff8e1;
  }

  h3 {
    margin-top: 0;
    color: #333;
  }

  h4 {
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
    color: #555;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: #555;
  }

  textarea {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #ddd;
    border-radius: 4px;
    font-family: inherit;
    font-size: 1rem;
    resize: vertical;
    box-sizing: border-box;
  }

  textarea:focus {
    outline: none;
    border-color: #667eea;
  }

  .button-group {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  button {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 600;
    transition: all 0.2s;
  }

  .submit-btn {
    background: #667eea;
    color: white;
    flex: 1;
  }

  .submit-btn:hover:not(:disabled) {
    background: #5568d3;
  }

  .submit-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
  }

  .clear-btn {
    background: #ff6b6b;
    color: white;
  }

  .clear-btn:hover:not(:disabled) {
    background: #ee5a52;
  }

  .clear-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
  }

  .error-message {
    padding: 1rem;
    background: #fee;
    border: 1px solid #fcc;
    border-radius: 4px;
    color: #c00;
    margin-top: 1rem;
  }

  .current-narrative {
    padding: 1rem;
    background: #e8f5e9;
    border: 2px solid #4caf50;
    border-radius: 4px;
    margin-top: 1rem;
  }

  .current-narrative h4 {
    margin-top: 0;
    color: #2e7d32;
  }
  
  .action-info {
    margin-top: 0.75rem;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .action-info code {
    display: block;
    margin-top: 0.25rem;
    padding: 0.5rem;
    background: #f5f5f5;
    border-radius: 3px;
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 0.85rem;
    overflow-x: auto;
    white-space: pre-wrap;
  }

  .current-narrative p {
    margin: 0;
    line-height: 1.6;
  }

  .history {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 2px solid #ddd;
  }

  .turn {
    padding: 1rem;
    margin-bottom: 1rem;
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
  .turn-action {
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: #f5f5f5;
    border-radius: 3px;
    font-size: 0.85rem;
  }

  .turn-action code {
    font-family: 'Monaco', 'Courier New', monospace;
    color: #666;
  }

  }

  .turn-number {
    font-size: 0.85rem;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.5rem;
  }

  .turn-input {
    margin-bottom: 0.5rem;
    color: #333;
  }

  .turn-narrative {
    color: #555;
    line-height: 1.5;
  }

  strong {
    color: #333;
  }
</style>
