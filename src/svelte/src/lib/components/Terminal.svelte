<script lang="ts">
  import type { Message } from '$lib/utils/messageLogger.svelte';
  import type { Snippet } from 'svelte';
  
  interface Props {
    title: string;
    messages: Message[];
    connected?: boolean;
    loading?: boolean;
    userInput?: string;
    onSubmit?: (input: string) => void;
    showInput?: boolean;
    linkHref?: string;
    linkText?: string;
    footerContent?: Snippet;
  }

  let {
    title,
    messages,
    connected = false,
    loading = false,
    userInput = $bindable(''),
    onSubmit,
    showInput = true,
    linkHref,
    linkText,
    footerContent
  }: Props = $props();

  let terminalRef = $state<HTMLDivElement | null>(null);
  let inputRef = $state<HTMLInputElement | null>(null);

  // scroll to bottom when messages change
  $effect(() => {
    if (messages.length && terminalRef) {
      terminalRef.scrollTop = terminalRef.scrollHeight;
    }
  });

  // refocus input after loading completes
  $effect(() => {
    if (!loading && inputRef) {
      inputRef.focus();
    }
  });

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !loading && userInput.trim()) {
      onSubmit?.(userInput);
    }
  }

  function focusInput() {
    inputRef?.focus();
  }
</script>

<div class="terminal-container" onclick={focusInput} role="presentation">
  <div class="terminal-header">
    <span class="terminal-title">{title}</span>
    {#if linkHref && linkText}
      <a href={linkHref} class="terminal-link">[{linkText}]</a>
    {/if}
  </div>
  
  <div class="terminal-body" bind:this={terminalRef}>
    {#each messages as message}
      <div class="terminal-line {message.type}">
        {#if message.type === 'system'}
          <span class="system-text">{message.text}</span>
        {:else if message.type === 'input'}
          <span class="input-text">{message.text}</span>
        {:else if message.type === 'output'}
          <span class="output-text">{message.text}</span>
        {:else if message.type === 'success'}
          <span class="success-text">{message.text}</span>
        {:else if message.type === 'error'}
          <span class="error-text">{message.text}</span>
        {/if}
      </div>
    {/each}
    
    {#if loading}
      <div class="terminal-line">
        <span class="system-text">processing<span class="blink">_</span></span>
      </div>
    {/if}

    {#if showInput && !loading}
      <div class="input-line">
        <span class="prompt">&gt;</span>
        <input
          type="text"
          bind:value={userInput}
          bind:this={inputRef}
          onkeydown={handleKeydown}
          disabled={loading}
          placeholder={''}
          class="terminal-input"
          autocomplete="off"
          spellcheck="false"
        />
      </div>
    {/if}

    {#if footerContent}
      {@render footerContent()}
    {/if}
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

  .success-text {
    color: #aaa;
  }

  .error-text {
    color: #fff;
    font-weight: bold;
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

  .cursor.blink,
  .blink {
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
