<script lang="ts">
  import type { Session } from '../../lib/types';
  import { activeSessionId, sessions as allSessions, closeTab, addSession } from '../../lib/stores';

  export let sessions: Session[];
  export let activeId: string | null;

  // New tab inherits the active session's data source
  $: activeDataSourceId =
    $allSessions.find(s => s.id === activeId)?.dataSourceId ?? null;
</script>

<div class="tab-strip">
  {#each sessions as session (session.id)}
    <button
      class="tab"
      class:active={session.id === activeId}
      on:click={() => activeSessionId.set(session.id)}
    >
      <span class="tab-title">{session.title}</span>
      <button
        class="close-btn"
        on:click|stopPropagation={() => closeTab(session.id)}
        aria-label="close tab"
      >×</button>
    </button>
  {/each}

  <button
    class="add-tab"
    on:click={() => addSession(activeDataSourceId)}
    title="New conversation"
  >
    +
  </button>
</div>

<style>
  .tab-strip {
    display: flex;
    align-items: flex-end;
    gap: 2px;
    overflow-x: auto;
    padding: 6px 8px 0;
    scrollbar-width: none;
    flex-shrink: 0;
    background: #0d1117;
    border-bottom: 1px solid #1f2937;
  }
  .tab-strip::-webkit-scrollbar { display: none; }

  .tab {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: #1a2130;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 6px 6px 0 0;
    color: #9ca3af;
    font-size: 12.5px;
    cursor: pointer;
    white-space: nowrap;
    min-width: 110px;
    max-width: 180px;
    flex-shrink: 0;
    height: 34px;
    transition: background 0.1s, color 0.1s, border-color 0.1s;
  }
  .tab:hover { background: #253040; color: #e5e7eb; }
  .tab.active {
    background: #0f172a;
    color: #f9fafb;
    border-bottom-color: #3b82f6;
  }

  .tab-title {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    text-align: left;
  }

  .close-btn {
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
    font-size: 15px;
    padding: 0 2px;
    line-height: 1;
    border-radius: 3px;
    opacity: 0.5;
    flex-shrink: 0;
  }
  .close-btn:hover { opacity: 1; background: rgba(255,255,255,0.1); }

  .add-tab {
    background: none;
    border: none;
    color: #6b7280;
    font-size: 20px;
    cursor: pointer;
    padding: 0 8px;
    border-radius: 4px;
    flex-shrink: 0;
    line-height: 34px;
    height: 34px;
    align-self: flex-end;
  }
  .add-tab:hover { background: #1f2937; color: #e5e7eb; }
</style>
