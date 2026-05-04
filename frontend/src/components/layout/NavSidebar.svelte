<script lang="ts">
  import { activeMenu, sidebarCollapsed, dataSources, sessions, activeSessionId, openOrCreateSession } from '../../lib/stores';
  import { t } from '../../lib/i18n';
  import type { DataSource } from '../../lib/types';

  let sqlExpanded = true;

  // Auto-expand when a SQL session is active
  $: if ($activeMenu === 'sql-assistant') sqlExpanded = true;

  // Linked selection: highlight the connection that owns the active session
  $: linkedDataSourceId =
    $sessions.find(s => s.id === $activeSessionId)?.dataSourceId ?? null;

  const bottomItems = [
    { id: 'data-analysis', label: 'Data Analysis', icon: '📊' },
    { id: 'dashboard',     label: 'Dashboard',     icon: '📈' },
  ];

  function handleConnection(source: DataSource) {
    openOrCreateSession(source);
  }
</script>

<nav class="nav-sidebar" class:collapsed={$sidebarCollapsed}>
  <div class="sidebar-top">
    {#if !$sidebarCollapsed}
      <span class="sidebar-title">Menu</span>
    {/if}
    <button
      class="toggle-btn"
      on:click={() => sidebarCollapsed.update(v => !v)}
      title={$sidebarCollapsed ? $t('nav.expand') : $t('nav.collapse')}
      aria-label={$sidebarCollapsed ? $t('nav.expand') : $t('nav.collapse')}
    >
      {$sidebarCollapsed ? '▶' : '◀'}
    </button>
  </div>

  <div class="nav-items">
    <!-- SQL Assistant accordion -->
    <div class="accordion">
      <button
        class="nav-item accordion-header"
        class:active={$activeMenu === 'sql-assistant'}
        on:click={() => { sqlExpanded = !sqlExpanded; }}
        title="SQL Assistant"
      >
        <span class="icon">✨</span>
        {#if !$sidebarCollapsed}
          <span class="label">SQL Assistant</span>
          <span class="chevron" class:open={sqlExpanded}>›</span>
        {/if}
      </button>

      {#if sqlExpanded && !$sidebarCollapsed}
        <div class="conn-list">
          {#each $dataSources as source (source.id)}
            <button
              class="conn-item"
              class:linked={source.id === linkedDataSourceId}
              on:click={() => handleConnection(source)}
              title={source.name}
            >
              <span class="conn-dot {source.status}"></span>
              <span class="conn-name">{source.name}</span>
              <span class="conn-type">{source.type}</span>
            </button>
          {/each}
          {#if $dataSources.length === 0}
            <div class="conn-empty">{$t('nav.noConnections')}</div>
          {/if}
        </div>
      {/if}

      <!-- Collapsed: show individual dots per source -->
      {#if $sidebarCollapsed}
        {#each $dataSources as source (source.id)}
          <button
            class="conn-item-collapsed"
            on:click={() => handleConnection(source)}
            title={source.name}
          >
            <span class="conn-dot {source.status}"></span>
          </button>
        {/each}
      {/if}
    </div>

    <!-- Data Analysis + Dashboard -->
    {#each bottomItems as item}
      <button
        class="nav-item"
        class:active={$activeMenu === item.id}
        on:click={() => activeMenu.set(item.id)}
        title={item.label}
      >
        <span class="icon">{item.icon}</span>
        {#if !$sidebarCollapsed}
          <span class="label">{item.label}</span>
        {/if}
      </button>
    {/each}
  </div>

  <div class="sidebar-footer">
    {#if !$sidebarCollapsed}
      <span class="version">v0.1.0</span>
    {/if}
  </div>
</nav>

<style>
  .nav-sidebar {
    width: 300px;
    flex-shrink: 0;
    background: #111827;
    border-right: 1px solid #1f2937;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transition: width 0.2s ease;
  }
  .nav-sidebar.collapsed { width: 48px; }

  .sidebar-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 10px;
    border-bottom: 1px solid #1f2937;
    flex-shrink: 0;
    gap: 6px;
    min-height: 48px;
  }
  .nav-sidebar.collapsed .sidebar-top { justify-content: center; }

  .sidebar-title {
    font-size: 13px;
    font-weight: 700;
    color: #e5e7eb;
    letter-spacing: 0.3px;
    text-align: center;
    flex: 1;
  }

  .toggle-btn {
    background: transparent;
    border: none;
    color: #9ca3af;
    font-size: 12px;
    cursor: pointer;
    padding: 5px 7px;
    border-radius: 4px;
    flex-shrink: 0;
    line-height: 1;
  }
  .toggle-btn:hover { background: #1f2937; color: #e5e7eb; }

  .nav-items {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 8px 6px;
    flex: 1;
    overflow-y: auto;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    color: #d1d5db;
    padding: 10px 12px;
    border-radius: 7px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background 0.1s, color 0.1s;
    white-space: nowrap;
    overflow: hidden;
  }
  .nav-item:hover { background: #1f2937; color: #f3f4f6; }
  .nav-item.active { background: #1e3a5f; color: #93c5fd; }
  .nav-sidebar.collapsed .nav-item { justify-content: center; padding: 10px 0; }

  .icon { font-size: 17px; flex-shrink: 0; }
  .label { flex: 1; }

  /* Accordion chevron */
  .chevron {
    font-size: 14px;
    color: #4b5563;
    transform: rotate(90deg);
    transition: transform 0.15s;
    display: inline-block;
    flex-shrink: 0;
  }
  .chevron.open { transform: rotate(-90deg); }

  /* Connection list */
  .accordion { display: flex; flex-direction: column; }

  .conn-list {
    display: flex;
    flex-direction: column;
    margin: 2px 0 4px 12px;
    border-left: 1px solid #1f2937;
    padding-left: 8px;
  }

  .conn-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 6px;
    border: none;
    background: transparent;
    cursor: pointer;
    font-size: 13px;
    color: #c4c9d4;
    text-align: left;
    transition: background 0.1s, color 0.1s;
    white-space: nowrap;
    overflow: hidden;
  }
  .conn-item:hover { background: #1f2937; color: #f3f4f6; }
  .conn-item.linked { background: #1e3a5f; color: #93c5fd; }
  .conn-item.linked .conn-dot.connected { box-shadow: 0 0 6px #22c55ecc; }

  .conn-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .conn-dot.connected    { background: #22c55e; box-shadow: 0 0 4px #22c55e88; }
  .conn-dot.disconnected { background: #4b5563; }
  .conn-dot.error        { background: #ef4444; }

  .conn-name { flex: 1; overflow: hidden; text-overflow: ellipsis; }
  .conn-type { font-size: 10px; color: #4b5563; flex-shrink: 0; }

  .conn-empty {
    padding: 8px 10px;
    font-size: 12px;
    color: #4b5563;
    font-style: italic;
  }

  /* Collapsed mode: small dots only */
  .conn-item-collapsed {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: 6px 0;
    border: none;
    background: transparent;
    cursor: pointer;
  }
  .conn-item-collapsed:hover .conn-dot { transform: scale(1.4); }

  .sidebar-footer {
    padding: 10px 14px;
    border-top: 1px solid #1f2937;
    flex-shrink: 0;
    min-height: 40px;
    display: flex;
    align-items: center;
  }
  .version { font-size: 11px; color: #4b5563; }
</style>
