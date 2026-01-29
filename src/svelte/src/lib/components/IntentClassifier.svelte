<script lang="ts">
  import { apiClient, ApiError, type ClassifyIntentResponse } from '$lib/api/client';

  let userInput = $state('');
  let result = $state<ClassifyIntentResponse | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);

  async function handleClassify() {
    if (!userInput.trim()) {
      error = 'Please enter some text to classify';
      return;
    }

    loading = true;
    error = null;
    result = null;

    try {
      const response = await apiClient.classifyIntent({
        user_input: userInput.trim(),
      });
      result = response;
    } catch (err) {
      if (err instanceof ApiError) {
        error = `API Error: ${err.detail}`;
      } else {
        error = err instanceof Error ? err.message : 'Failed to classify intent';
      }
    } finally {
      loading = false;
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
      handleClassify();
    }
  }

  function getConfidenceColor(confidence: number): string {
    if (confidence >= 0.8) return '#28a745';
    if (confidence >= 0.5) return '#ffc107';
    return '#dc3545';
  }
</script>

<div class="intent-classifier">
  <h3>🎯 Intent Classifier</h3>
  
  <div class="form-group">
    <label for="user-input">User Input</label>
    <textarea
      id="user-input"
      bind:value={userInput}
      onkeydown={handleKeydown}
      placeholder="Enter user input to classify... (Cmd/Ctrl+Enter to submit)"
      rows="3"
    ></textarea>
  </div>

  <button 
    onclick={handleClassify} 
    disabled={loading || !userInput.trim()}
    class="classify-btn"
  >
    {loading ? 'Classifying...' : 'Classify Intent'}
  </button>

  {#if error}
    <div class="error-message">
      ❌ {error}
    </div>
  {/if}

  {#if result}
    <div class="result">
      <h4>Classification Result:</h4>
      <div class="result-grid">
        <div class="result-item">
          <span class="label">Action:</span>
          <span class="value action">{result.action}</span>
        </div>
        <div class="result-item">
          <span class="label">Target:</span>
          <span class="value target">{result.target || '(none)'}</span>
        </div>
        <div class="result-item">
          <span class="label">Confidence:</span>
          <span 
            class="value confidence"
            style="color: {getConfidenceColor(result.confidence)}"
          >
            {(result.confidence * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .intent-classifier {
    padding: 1.5rem;
    border: 2px solid #333;
    border-radius: 8px;
    margin-bottom: 2rem;
    background: #fff8f0;
  }

  h3 {
    margin-top: 0;
    color: #333;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #333;
  }

  textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-family: inherit;
    font-size: 0.95rem;
    resize: vertical;
  }

  textarea:focus {
    outline: none;
    border-color: #ff6b35;
    box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.1);
  }

  .classify-btn {
    width: 100%;
    padding: 0.75rem;
    background: #ff6b35;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 500;
  }

  .classify-btn:hover:not(:disabled) {
    background: #e55a28;
  }

  .classify-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }

  .error-message {
    margin-top: 1rem;
    padding: 0.75rem;
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    color: #721c24;
  }

  .result {
    margin-top: 1.5rem;
    padding: 1rem;
    background: white;
    border: 1px solid #ff6b35;
    border-radius: 4px;
  }

  .result h4 {
    margin-top: 0;
    color: #ff6b35;
  }

  .result-grid {
    display: grid;
    gap: 0.75rem;
  }

  .result-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    background: #f8f9fa;
    border-radius: 4px;
  }

  .label {
    font-weight: 500;
    color: #666;
  }

  .value {
    font-weight: 600;
    font-size: 1.1rem;
  }

  .value.action {
    color: #007bff;
  }

  .value.target {
    color: #6610f2;
  }

  .value.confidence {
    font-weight: 700;
  }
</style>
