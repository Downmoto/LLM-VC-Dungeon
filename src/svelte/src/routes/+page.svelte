<script lang="ts">
  import { ApiStatus, TextGenerator, IntentClassifier, GameTurn } from '$lib';
</script>

<div class="container">
  <header>
    <h1>LLM Voice-Controlled Dungeon</h1>
    <p>FastAPI + Svelte Frontend Boilerplate</p>
  </header>

  <main>
    <ApiStatus />
    <GameTurn />
    <TextGenerator />
    <IntentClassifier />
  </main>

  <footer>
    <p>Backend running on <code>http://localhost:8000</code></p>
    <p>Frontend running on <code>http://localhost:5173</code></p>
  </footer>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
  }

  .container {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
  }

  header {
    text-align: center;
    color: white;
    margin-bottom: 3rem;
  }

  header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
  }

  header p {
    font-size: 1.1rem;
    opacity: 0.9;
  }

  main {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  }

  footer {
    text-align: center;
    color: white;
    margin-top: 2rem;
    opacity: 0.8;
    font-size: 0.9rem;
  }

  footer p {
    margin: 0.25rem 0;
  }

  code {
    background: rgba(255, 255, 255, 0.2);
    padding: 0.2rem 0.5rem;
    border-radius: 3px;
    font-family: 'Monaco', 'Courier New', monospace;
  }
</style>
