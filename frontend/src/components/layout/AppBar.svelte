<script lang="ts">
  import { sidebarCollapsed, activeMenu } from '../../lib/stores';
  import { language, t } from '../../lib/i18n';

  $: nameWidth = $sidebarCollapsed ? 48 : 300;

  let langOpen = false;

  const LANGUAGES: { code: 'en' | 'ko'; label: string }[] = [
    { code: 'en', label: 'English' },
    { code: 'ko', label: '한국어' },
  ];

  $: currentLabel = LANGUAGES.find(l => l.code === $language)?.label ?? 'English';

  function clickOutside(node: HTMLElement, callback: () => void) {
    const handleClick = (e: MouseEvent) => {
      if (!node.contains(e.target as Node)) callback();
    };
    document.addEventListener('mousedown', handleClick);
    return { destroy() { document.removeEventListener('mousedown', handleClick); } };
  }
</script>

<header class="app-bar">
  <button class="app-name" style="width: {nameWidth}px" on:click={() => location.reload()} title={$t('appbar.home.title')}>
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
    <!-- Language selector -->
    <div class="lang-selector" use:clickOutside={() => langOpen = false}>
      <button class="lang-trigger" on:click={() => langOpen = !langOpen} aria-expanded={langOpen}>
        <span class="lang-current">{currentLabel}</span>
        <span class="lang-chevron" class:open={langOpen}>›</span>
      </button>

      {#if langOpen}
        <div class="lang-dropdown" role="listbox">
          {#each LANGUAGES as lang}
            <button
              class="lang-option"
              class:active={$language === lang.code}
              role="option"
              aria-selected={$language === lang.code}
              on:click={() => { language.set(lang.code); langOpen = false; }}
            >
              {lang.label}
            </button>
          {/each}
        </div>
      {/if}
    </div>

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

  /* Right side */
  .profile-area {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 12px;
    flex-shrink: 0;
    border-left: 1px solid #1f2937;
  }

  /* Language selector */
  .lang-selector {
    position: relative;
  }

  .lang-trigger {
    display: flex;
    align-items: center;
    gap: 6px;
    height: 32px;
    width: 100px;
    padding: 0 12px;
    background: transparent;
    border: 1px solid #374151;
    border-radius: 6px;
    color: #d1d5db;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.15s, border-color 0.15s;
  }
  .lang-trigger:hover { background: #1f2937; border-color: #4b5563; }

  .lang-current { line-height: 1; }

  .lang-chevron {
    font-size: 16px;
    color: #6b7280;
    transform: rotate(90deg);
    transition: transform 0.15s;
    display: inline-block;
    line-height: 1;
  }
  .lang-chevron.open { transform: rotate(-90deg); }

  .lang-dropdown {
    position: absolute;
    top: calc(100% + 6px);
    right: 0;
    min-width: 140px;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
    z-index: 200;
  }

  .lang-option {
    display: block;
    width: 100%;
    padding: 11px 16px;
    background: transparent;
    border: none;
    border-bottom: 1px solid #f3f4f6;
    font-size: 14px;
    text-align: left;
    cursor: pointer;
    color: #374151;
    transition: background 0.1s;
  }
  .lang-option:last-child { border-bottom: none; }
  .lang-option:hover { background: #f3f4f6; }
  .lang-option.active {
    font-weight: 600;
    color: #1d4ed8;
    background: #eff6ff;
  }

  /* Profile button */
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
    color: #e5e7eb;
    flex-shrink: 0;
  }
  .profile-btn:hover { background: #1f2937; }
</style>
