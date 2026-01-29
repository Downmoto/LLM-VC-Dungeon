<script lang="ts">
  import { apiClient, ApiError } from '$lib/api/client';

  let prompt = $state('');
  let systemPrompt = $state('You are a helpful assistant for a dungeon crawler game.');
  let generatedText = $state<string | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);

  async function handleGenerate() {
    if (!prompt.trim()) {
      error = 'Please enter a prompt';
      return;
    }

    loading = true;
    error = null;
    generatedText = null;

    try {
      const response = await apiClient.generateText({
        prompt: prompt.trim(),
        system_prompt: systemPrompt.trim() || undefined,
      });
      generatedText = response.text;
    } catch (err) {
      if (err instanceof ApiError) {
        error = `API Error: ${err.detail}`;
      } else {
        error = err instanceof Error ? err.message : 'Failed to generate text';
      }
    } finally {
      loading = false;
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
      handleGenerate();
    }
  }
</script>

<div class="text-generator">
  <h3>📝 Text Generator</h3>
  
  <div class="form-group">
    <label for="system-prompt">System Prompt (optional)</label>
    <textarea
      id="system-prompt"
      bind:value={systemPrompt}
      placeholder="Enter system prompt..."
      rows="2"
    ></textarea>
  </div>

  <div class="form-group">
    <label for="prompt">Prompt</label>
    <textarea
      id="prompt"
      bind:value={prompt}
      onkeydown={handleKeydown}
      placeholder="Enter your prompt... (Cmd/Ctrl+Enter to submit)"
      rows="4"
    ></textarea>
  </div>

  <button 
    onclick={handleGenerate} 
    disabled={loading || !prompt.trim()}
    class="generate-btn"
  >
    {loading ? 'Generating...' : 'Generate Text'}
  </button>

  {#if error}
    <div class="error-message">
      ❌ {error}
    </div>
  {/if}

  {#if generatedText}
    <div class="result">
      <h4>Generated Text:</h4>
      <p>{generatedText}</p>
    </div>
  {/if}
</div>

<style>
  .text-generator {
    padding: 1.5rem;
    border: 2px solid #333;
    border-radius: 8px;
    margin-bottom: 2rem;
    background: #f0f8ff;
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
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
  }

  .generate-btn {
    width: 100%;
    padding: 0.75rem;
    background: #28a745;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 500;
  }

  .generate-btn:hover:not(:disabled) {
    background: #218838;
  }

  .generate-btn:disabled {
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
    border: 1px solid #28a745;
    border-radius: 4px;
  }

  .result h4 {
    margin-top: 0;
    color: #28a745;
  }

  .result p {
    margin: 0;
    line-height: 1.6;
    white-space: pre-wrap;
  }
</style>
