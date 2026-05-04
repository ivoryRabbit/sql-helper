<script lang="ts">
  import type { Session } from '../../lib/types';
  import { activeSessionId, openSessionInTab, removeSession, dataSources } from '../../lib/stores';
  import { language, t } from '../../lib/i18n';

  export let sessions: Session[];

  // Most recent 10, displayed newest-first
  $: recentSessions = [...sessions].reverse().slice(0, 10);

  $: dateLocale = $language === 'ko' ? 'ko-KR' : 'en-US';

  function formatDate(d: Date): string {
    return new Intl.DateTimeFormat(dateLocale, {
      month: 'short',
      day: 'numeric',
    }).format(d);
  }

  function getSourceName(dataSourceId: string | null): string | null {
    if (!dataSourceId) return null;
    return $dataSources.find(s => s.id === dataSourceId)?.name ?? null;
  }
</script>

<div class="session-panel">
  <div class="panel-header">
    <p class="panel-title">Conversations</p>
  </div>

  <div class="session-list">
    <p class="list-label">Recent ({recentSessions.length})</p>
    {#each recentSessions as session (session.id)}
      {@const sourceName = getSourceName(session.dataSourceId)}
      <div
        class="session-item"
        class:active={session.id === $activeSessionId}
      >
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <div class="session-body" role="button" tabindex="0" on:click={() => openSessionInTab(session.id)}>
          <span class="title">{session.title}</span>
          <div class="session-meta">
            <span class="date">{formatDate(session.createdAt)}</span>
            {#if sourceName}
              <span class="conn-badge">{sourceName}</span>
            {/if}
          </div>
        </div>
        <button
          class="delete-btn"
          aria-label={$t('session.delete.label')}
          title={$t('session.delete.label')}
          on:click|stopPropagation={() => removeSession(session.id)}
        >🗑</button>
      </div>
    {/each}
  </div>
</div>

<style>
  .session-panel {
    width: 240px;
    flex-shrink: 0;
    background: #111827;
    border-left: 1px solid #1f2937;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    align-items: center;
    padding: 12px 12px 10px;
    border-bottom: 1px solid #1f2937;
    flex-shrink: 0;
    min-height: 48px;
  }

  .panel-title {
    margin: 0;
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .session-list {
    flex: 1;
    overflow-y: auto;
    padding: 6px 8px;
  }

  .list-label {
    font-size: 11px;
    font-weight: 600;
    color: #4b5563;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin: 4px 4px 6px;
  }

  .session-item {
    display: flex;
    align-items: center;
    gap: 4px;
    border-radius: 6px;
    transition: background 0.1s;
    padding-right: 2px;
  }
  .session-item:hover { background: #1f2937; }
  .session-item.active { background: #1e3a5f; }

  .session-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding: 8px 6px 8px 10px;
    cursor: pointer;
    min-width: 0;
  }

  .title {
    font-size: 13px;
    color: #e5e7eb;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .session-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    gap: 6px;
  }

  .date {
    font-size: 11px;
    color: #6b7280;
    flex-shrink: 0;
  }

  .conn-badge {
    font-size: 10px;
    color: #60a5fa;
    background: #1e3a5f;
    border-radius: 3px;
    padding: 1px 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100px;
  }

  .delete-btn {
    flex-shrink: 0;
    width: 26px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    border-radius: 4px;
    font-size: 13px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.1s, background 0.1s;
    color: #6b7280;
  }
  .session-item:hover .delete-btn { opacity: 1; }
  .delete-btn:hover { background: #374151; color: #ef4444; }
</style>
