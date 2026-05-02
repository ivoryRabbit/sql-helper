<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let hasPendingSql = false;

  const dispatch = createEventDispatcher<{
    send: { text: string };
    save: void;
    analyze: void;
  }>();

  let text = '';
  let textarea: HTMLTextAreaElement;

  function resize() {
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function send() {
    const trimmed = text.trim();
    if (!trimmed) return;
    dispatch('send', { text: trimmed });
    text = '';
    if (textarea) textarea.style.height = 'auto';
  }
</script>

<div class="input-bar">
  <textarea
    bind:this={textarea}
    bind:value={text}
    on:input={resize}
    on:keydown={handleKeydown}
    placeholder="데이터에 대해 질문하세요...  (Enter 전송, Shift+Enter 줄바꿈)"
    rows="1"
  ></textarea>

  <div class="actions">
    <button class="btn-secondary" on:click={() => dispatch('save')}>
      Save conversation
    </button>
    <button
      class="btn-primary"
      class:disabled={!hasPendingSql}
      disabled={!hasPendingSql}
      on:click={() => dispatch('analyze')}
    >
      Go to analysis
    </button>
  </div>
</div>

<style>
  .input-bar {
    padding: 12px 16px 14px;
    background: #1a2332;
    border-top: 1px solid #1f2937;
    display: flex;
    flex-direction: column;
    gap: 10px;
    flex-shrink: 0;
  }

  textarea {
    width: 100%;
    background: #111827;
    color: #f9fafb;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
    font-family: inherit;
    resize: none;
    min-height: 42px;
    overflow-y: hidden;
    box-sizing: border-box;
    line-height: 1.5;
  }
  textarea::placeholder { color: #4b5563; }
  textarea:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  }

  .actions {
    display: flex;
    justify-content: space-between;
    gap: 8px;
  }

  .btn-secondary,
  .btn-primary {
    padding: 7px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: background 0.1s;
  }

  .btn-secondary {
    background: #374151;
    color: #d1d5db;
  }
  .btn-secondary:hover { background: #4b5563; }

  .btn-primary {
    background: #2563eb;
    color: #fff;
  }
  .btn-primary:hover:not(:disabled) { background: #1d4ed8; }
  .btn-primary:disabled,
  .btn-primary.disabled {
    background: #1e3160;
    color: #4b6cb7;
    cursor: not-allowed;
  }
</style>
