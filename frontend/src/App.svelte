<script lang="ts">
  import { onMount } from 'svelte';
  import { sessions, openTabIds, activeSessionId, activeMenu, dataSources, selectedDataSource } from './lib/stores';
  import { dataSourceApi } from './lib/api';
  import { t } from './lib/i18n';
  import AppBar from './components/layout/AppBar.svelte';
  import NavSidebar from './components/layout/NavSidebar.svelte';
  import SessionPanel from './components/layout/SessionPanel.svelte';
  import TabStrip from './components/layout/TabStrip.svelte';
  import ConversationView from './components/conversation/ConversationView.svelte';
  import DataSource from './components/DataSource.svelte';
  import DataCatalog from './components/DataCatalog.svelte';
  import TextToSQL from './components/TextToSQL.svelte';
  import DataAnalysis from './components/DataAnalysis.svelte';
  import Dashboard from './components/Dashboard.svelte';

  $: openTabSessions = $sessions.filter(s => $openTabIds.includes(s.id));

  onMount(async () => {
    try {
      const list = await dataSourceApi.list();
      dataSources.set(list);
      if (list.length > 0) selectedDataSource.set(list[0]);
    } catch {
      // Backend unreachable — leave dataSources empty; user can add a Mockup source manually
    }
  });
</script>

<div class="shell">
  <AppBar />

  <div class="body">
    <NavSidebar />

    <main class="main" class:dark={$activeMenu === 'sql-assistant'}>
      {#if $activeMenu === 'sql-assistant'}
        {#if $dataSources.length === 0}
          <div class="no-tabs-landing">
            <div class="landing-icon">🗄️</div>
            <p class="landing-title">{$t('app.noSources.title')}</p>
            <p class="landing-hint">{$t('app.noSources.hint')}</p>
            <button class="landing-cta" on:click={() => activeMenu.set('data-source')}>
              {$t('app.noSources.cta')}
            </button>
          </div>
        {:else}
          <TabStrip sessions={openTabSessions} activeId={$activeSessionId} />
          <div class="sql-body">
            {#if openTabSessions.length === 0}
              <div class="no-tabs-landing">
                <div class="landing-icon">✨</div>
                <p class="landing-title">{$t('app.noTabs.title')}</p>
                <p class="landing-hint">{$t('app.noTabs.hint')}</p>
              </div>
            {:else}
              <!-- key resets async state (isLoading) on session switch -->
              {#key $activeSessionId}
                <ConversationView />
              {/key}
            {/if}
            <SessionPanel sessions={$sessions} />
          </div>
        {/if}
      {:else if $activeMenu === 'data-source'}
        <DataSource />
      {:else if $activeMenu === 'data-catalog'}
        <DataCatalog />
      {:else if $activeMenu === 'text-to-sql'}
        <TextToSQL />
      {:else if $activeMenu === 'data-analysis'}
        <DataAnalysis />
      {:else if $activeMenu === 'dashboard'}
        <Dashboard />
      {/if}
    </main>
  </div>
</div>

<style>
  :global(*) { box-sizing: border-box; }
  :global(body) { margin: 0; font-family: system-ui, -apple-system, sans-serif; }

  .shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
    background: #111827;
  }

  .body {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  .main {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    min-width: 0;
    background: #f9fafb;
  }

  .main.dark {
    background: #0f172a;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .sql-body {
    display: flex;
    flex-direction: row;
    flex: 1;
    overflow: hidden;
    min-height: 0;
  }

  .no-tabs-landing {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: #4b5563;
  }

  .landing-icon { font-size: 48px; line-height: 1; }

  .landing-title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #9ca3af;
  }

  .landing-hint {
    margin: 0;
    font-size: 13px;
    color: #4b5563;
  }

  .landing-cta {
    margin-top: 8px;
    padding: 10px 22px;
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s;
  }
  .landing-cta:hover { background: #1d4ed8; }
</style>
