<script lang="ts">
  import { afterUpdate } from 'svelte';
  import type { ChatMessage } from '../lib/types';
  import { generateMockSQL } from '../lib/mock';

  let messages: ChatMessage[] = [
    {
      id: '0',
      role: 'assistant',
      content: '안녕하세요! 자연어로 질문하면 SQL을 생성해 드립니다.\n\n예시:\n• "최근 3개월 월별 매출 알려줘"\n• "Pro 등급 고객이 몇 명이야?"\n• "카테고리별 상품 평균 가격"',
      timestamp: new Date(),
    },
  ];

  let inputText = '';
  let isGenerating = false;
  let listEl: HTMLElement;

  afterUpdate(() => {
    if (listEl) listEl.scrollTop = listEl.scrollHeight;
  });

  function uid() {
    return Math.random().toString(36).slice(2);
  }

  async function send() {
    const text = inputText.trim();
    if (!text || isGenerating) return;

    inputText = '';
    messages = [
      ...messages,
      { id: uid(), role: 'user', content: text, timestamp: new Date() },
    ];

    isGenerating = true;

    // Simulate a short delay for generation
    await new Promise(r => setTimeout(r, 600 + Math.random() * 600));

    const { sql, explanation } = generateMockSQL(text);
    messages = [
      ...messages,
      {
        id: uid(),
        role: 'assistant',
        content: explanation,
        sql,
        timestamp: new Date(),
      },
    ];

    isGenerating = false;
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function clearHistory() {
    messages = [messages[0]];
  }

  function copySQL(sql: string) {
    navigator.clipboard.writeText(sql).catch(() => {});
  }

  function formatTime(d: Date) {
    return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
  }
</script>

<aside class="chat-panel">
  <header class="chat-header">
    <span class="chat-title">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      SQL Assistant
    </span>
    <button class="clear-btn" on:click={clearHistory} title="대화 초기화">↺</button>
  </header>

  <div class="messages" bind:this={listEl}>
    {#each messages as msg (msg.id)}
      <div class="message {msg.role}">
        <div class="bubble">
          <p class="text">{msg.content}</p>
          {#if msg.sql}
            <div class="sql-block">
              <div class="sql-header">
                <span>SQL</span>
                <button class="copy-btn" on:click={() => copySQL(msg.sql)}>복사</button>
              </div>
              <pre class="sql-code">{msg.sql}</pre>
            </div>
          {/if}
        </div>
        <span class="ts">{formatTime(msg.timestamp)}</span>
      </div>
    {/each}

    {#if isGenerating}
      <div class="message assistant">
        <div class="bubble generating">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>
    {/if}
  </div>

  <div class="input-area">
    <textarea
      bind:value={inputText}
      on:keydown={onKeydown}
      placeholder="자연어로 질문하세요… (Enter 전송, Shift+Enter 줄바꿈)"
      rows="3"
      disabled={isGenerating}
    ></textarea>
    <button class="send-btn" on:click={send} disabled={isGenerating || !inputText.trim()}>
      {#if isGenerating}
        ···
      {:else}
        전송
      {/if}
    </button>
  </div>
</aside>

<style>
  .chat-panel {
    display: flex;
    flex-direction: column;
    width: 360px;
    min-width: 360px;
    background: #111827;
    border-left: 1px solid #1f2937;
    height: 100vh;
    overflow: hidden;
  }

  /* Header */
  .chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    border-bottom: 1px solid #1f2937;
    flex-shrink: 0;
  }
  .chat-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 14px;
    color: #e5e7eb;
  }
  .clear-btn {
    background: transparent;
    border: none;
    color: #6b7280;
    font-size: 18px;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 4px;
    line-height: 1;
  }
  .clear-btn:hover { color: #9ca3af; background: #1f2937; }

  /* Messages */
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    scroll-behavior: smooth;
  }
  .messages::-webkit-scrollbar { width: 4px; }
  .messages::-webkit-scrollbar-track { background: transparent; }
  .messages::-webkit-scrollbar-thumb { background: #374151; border-radius: 2px; }

  .message { display: flex; flex-direction: column; gap: 2px; }
  .message.user { align-items: flex-end; }
  .message.assistant { align-items: flex-start; }

  .bubble {
    max-width: 100%;
    border-radius: 12px;
    padding: 10px 12px;
    font-size: 13px;
    line-height: 1.5;
  }
  .message.user .bubble {
    background: #2563eb;
    color: #fff;
    border-bottom-right-radius: 4px;
  }
  .message.assistant .bubble {
    background: #1f2937;
    color: #e5e7eb;
    border-bottom-left-radius: 4px;
  }

  .text { margin: 0; white-space: pre-wrap; word-break: break-word; }

  /* SQL block */
  .sql-block {
    margin-top: 8px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #374151;
  }
  .sql-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 10px;
    background: #0f172a;
    font-size: 11px;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .copy-btn {
    background: transparent;
    border: none;
    color: #60a5fa;
    font-size: 11px;
    cursor: pointer;
    padding: 1px 4px;
  }
  .copy-btn:hover { text-decoration: underline; }
  .sql-code {
    margin: 0;
    padding: 10px;
    background: #0b1120;
    color: #93c5fd;
    font-size: 12px;
    font-family: 'Cascadia Code', 'Fira Code', monospace;
    white-space: pre;
    overflow-x: auto;
  }

  .ts {
    font-size: 10px;
    color: #4b5563;
    padding: 0 4px;
  }

  /* Generating animation */
  .generating {
    display: flex;
    gap: 5px;
    align-items: center;
    padding: 14px 16px;
  }
  .dot {
    width: 7px;
    height: 7px;
    background: #4b5563;
    border-radius: 50%;
    animation: blink 1.2s infinite both;
  }
  .dot:nth-child(2) { animation-delay: 0.2s; }
  .dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes blink {
    0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
    40% { opacity: 1; transform: scale(1); }
  }

  /* Input area */
  .input-area {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 10px 12px 12px;
    border-top: 1px solid #1f2937;
    flex-shrink: 0;
  }
  textarea {
    width: 100%;
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 8px;
    color: #e5e7eb;
    font-size: 13px;
    padding: 10px;
    resize: none;
    outline: none;
    font-family: inherit;
    line-height: 1.5;
  }
  textarea::placeholder { color: #4b5563; }
  textarea:focus { border-color: #2563eb; }
  textarea:disabled { opacity: 0.5; cursor: not-allowed; }

  .send-btn {
    width: 100%;
    background: #2563eb;
    border: none;
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 20px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.15s;
  }
  .send-btn:hover:not(:disabled) { background: #1d4ed8; }
  .send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
