<script lang="ts">
  import SqlBlock from './SqlBlock.svelte';
  import type { Message } from '../../lib/types';

  export let message: Message;

  function formatTime(d: Date): string {
    return new Intl.DateTimeFormat('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(d);
  }
</script>

<div class="wrapper" class:user={message.role === 'user'}>
  <div class="bubble" class:user={message.role === 'user'} class:assistant={message.role === 'assistant'}>
    <p class="content">{message.content}</p>

    {#if message.sql}
      <SqlBlock sql={message.sql} />
    {/if}

    {#if message.dataSources && message.dataSources.length > 0}
      <div class="sources">
        <span class="sources-label">Data source:</span>
        <ol>
          {#each message.dataSources as src, i}
            <li>{src}</li>
          {/each}
        </ol>
      </div>
    {/if}
  </div>
  <span class="time">{formatTime(message.createdAt)}</span>
</div>

<style>
  .wrapper {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    max-width: 78%;
    gap: 4px;
  }
  .wrapper.user {
    align-self: flex-end;
    align-items: flex-end;
  }

  .bubble {
    padding: 12px 16px;
    border-radius: 18px;
    line-height: 1.55;
    word-break: break-word;
  }
  .bubble.user {
    background: #2563eb;
    color: #fff;
    border-bottom-right-radius: 4px;
  }
  .bubble.assistant {
    background: #1f2937;
    color: #e5e7eb;
    border-bottom-left-radius: 4px;
  }

  .content {
    margin: 0;
    font-size: 14px;
    white-space: pre-wrap;
  }

  .sources {
    margin-top: 8px;
    font-size: 13px;
    color: #9ca3af;
  }
  .sources-label { font-weight: 600; }
  .sources ol {
    margin: 4px 0 0 16px;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .time {
    font-size: 11px;
    color: #6b7280;
  }
</style>
