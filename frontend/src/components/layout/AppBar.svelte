<script lang="ts">
  import { sidebarCollapsed, activeMenu } from '../../lib/stores';

  $: nameWidth = $sidebarCollapsed ? 48 : 300;
</script>

<header class="app-bar">
  <button class="app-name" style="width: {nameWidth}px" on:click={() => location.reload()} title="홈으로 (새로고침)">
    {#if !$sidebarCollapsed}
      <span class="logo">⚡</span>
      <span class="text">SQL Helper</span>
    {:else}
      <span class="logo">⚡</span>
    {/if}
  </button>

  <nav class="top-nav">
    <button
      class="top-nav-item"
      class:active={$activeMenu === 'data-source'}
      on:click={() => activeMenu.set('data-source')}
    >
      🗄️ Data Source
    </button>
    <button
      class="top-nav-item"
      class:active={$activeMenu === 'data-catalog'}
      on:click={() => activeMenu.set('data-catalog')}
    >
      📚 Data Catalog
    </button>
  </nav>

  <div class="profile-area">
    <button class="profile-btn" aria-label="Profile">👤</button>
  </div>
</header>

<style>
  .app-bar {
    height: 48px;
    background: #0d1117;
    border-bottom: 1px solid #1f2937;
    display: flex;
    align-items: stretch;
    flex-shrink: 0;
    overflow: hidden;
  }

  .app-name {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    flex-shrink: 0;
    border-right: 1px solid #1f2937;
    transition: width 0.2s ease;
    overflow: hidden;
    white-space: nowrap;
    background: transparent;
    border-top: none;
    border-bottom: none;
    border-left: none;
    cursor: pointer;
  }
  .app-name:hover { background: #161d2b; }

  .logo { font-size: 16px; }
  .text { font-size: 14px; font-weight: 700; color: #f9fafb; }

  .top-nav {
    display: flex;
    align-items: center;
    gap: 2px;
    padding: 0 12px;
    flex: 1;
  }

  .top-nav-item {
    display: flex;
    align-items: center;
    gap: 6px;
    height: 32px;
    padding: 0 14px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    color: #9ca3af;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.15s, color 0.15s;
  }
  .top-nav-item:hover { background: #1f2937; color: #e5e7eb; }
  .top-nav-item.active { background: #1e3a5f; color: #93c5fd; border-color: #1e40af; }

  .profile-area {
    display: flex;
    align-items: center;
    padding: 0 12px;
    flex-shrink: 0;
    border-left: 1px solid #1f2937;
  }

  .profile-btn {
    background: none;
    border: 1px solid #374151;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    cursor: pointer;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .profile-btn:hover { background: #1f2937; }
</style>
