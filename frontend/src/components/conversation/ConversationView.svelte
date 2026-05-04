<script lang="ts">
  import { afterUpdate } from 'svelte';
  import MessageBubble from './MessageBubble.svelte';
  import PromptInputBar from './PromptInputBar.svelte';
  import { sessions, activeSessionId, addMessage, activeMenu, pendingSql, selectedDataSource } from '../../lib/stores';
  import { textToSqlApi, ApiError } from '../../lib/api';
  import { t } from '../../lib/i18n';

  let messagesEl: HTMLDivElement;
  let isLoading = false;

  // Streaming state — rendered as a temporary bubble until generation_complete
  let streamingContent = '';
  let isStreaming = false;

  $: currentSession = $sessions.find(s => s.id === $activeSessionId);
  $: messages = currentSession?.messages ?? [];
  $: hasPendingSql = $pendingSql !== null;

  afterUpdate(() => {
    if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
  });

  async function handleSend(e: CustomEvent<{ text: string }>) {
    if (isLoading || !$activeSessionId) return;
    const { text } = e.detail;
    const sid = $activeSessionId;

    addMessage(sid, {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      createdAt: new Date(),
    });

    isLoading = true;
    isStreaming = true;
    streamingContent = '';

    try {
      for await (const event of textToSqlApi.generateSql({
        query: text,
        data_source_id: $selectedDataSource?.id ?? null,
        options: { include_explanation: true, sql_dialect: 'postgresql' },
      })) {
        if (event.type === 'sql_chunk') {
          streamingContent += event.content;
        } else if (event.type === 'generation_complete') {
          isStreaming = false;
          streamingContent = '';
          const sql = event.sql ?? undefined;
          addMessage(sid, {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: event.explanation ?? '',
            sql,
            dataSources: sql ? extractTables(sql) : undefined,
            createdAt: new Date(),
          });
          pendingSql.set(event.sql ?? null);
        } else if (event.type === 'error') {
          isStreaming = false;
          streamingContent = '';
          addMessage(sid, {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: $t('conv.error.sse', { message: event.message }),
            createdAt: new Date(),
          });
        }
      }
    } catch (err) {
      isStreaming = false;
      streamingContent = '';
      const msg = err instanceof ApiError ? err.message : String(err);
      addMessage(sid, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: $t('conv.error.request', { message: msg }),
        createdAt: new Date(),
      });
    } finally {
      isLoading = false;
      isStreaming = false;
    }
  }

  function handleSave() {
    // session persistence is frontend-local for now
  }

  function handleAnalyze() {
    activeMenu.set('data-analysis');
  }

  function extractTables(sql: string): string[] {
    const matches = sql.match(/(?:FROM|JOIN)\s+([\w.]+)/gi) ?? [];
    return [...new Set(matches.map(m => m.replace(/^(?:FROM|JOIN)\s+/i, '').trim()))];
  }
</script>

<div class="conversation">
  <div class="messages" bind:this={messagesEl}>
    {#each messages as message (message.id)}
      <MessageBubble {message} />
    {/each}

    {#if isStreaming && streamingContent}
      <div class="streaming-bubble">
        <pre class="streaming-text">{streamingContent}</pre>
      </div>
    {:else if isLoading}
      <div class="loading-bubble">
        <span></span><span></span><span></span>
      </div>
    {/if}
  </div>

  <PromptInputBar
    {hasPendingSql}
    on:send={handleSend}
    on:save={handleSave}
    on:analyze={handleAnalyze}
  />
</div>

<style>
  .conversation {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
    overflow: hidden;
    background: #0f172a;
  }

  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 24px 28px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .streaming-bubble {
    align-self: flex-start;
    max-width: 72%;
    background: #1f2937;
    border-radius: 18px;
    border-bottom-left-radius: 4px;
    padding: 14px 18px;
  }
  .streaming-text {
    margin: 0;
    color: #e5e7eb;
    font-family: 'Cascadia Code', 'Fira Mono', monospace;
    font-size: 13px;
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.6;
  }

  .loading-bubble {
    display: flex;
    gap: 5px;
    align-self: flex-start;
    padding: 14px 18px;
    background: #1f2937;
    border-radius: 18px;
    border-bottom-left-radius: 4px;
  }
  .loading-bubble span {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #6b7280;
    animation: pulse 1.2s ease-in-out infinite;
  }
  .loading-bubble span:nth-child(2) { animation-delay: 0.2s; }
  .loading-bubble span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes pulse {
    0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
    40%           { opacity: 1;   transform: scale(1);   }
  }
</style>
