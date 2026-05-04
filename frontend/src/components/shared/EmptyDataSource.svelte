<script lang="ts">
  import { activeMenu } from '../../lib/stores';
  import { t } from '../../lib/i18n';

  // 'none'   — no data sources registered at all
  // 'select' — sources exist but none selected
  export let reason: 'none' | 'select' = 'none';
</script>

<div class="empty-wrap">
  <div class="icon">{reason === 'none' ? '🗄️' : '📂'}</div>

  {#if reason === 'none'}
    <p class="title">{$t('empty.noSources.title')}</p>
    <p class="desc">{$t('empty.noSources.desc')}</p>
    <button class="cta" on:click={() => activeMenu.set('data-source')}>
      {$t('empty.noSources.cta')}
    </button>
  {:else}
    <p class="title">{$t('empty.noSelect.title')}</p>
    <p class="desc">{$t('empty.noSelect.desc')}</p>
  {/if}
</div>

<style>
  .empty-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 320px;
    gap: 12px;
    padding: 40px;
    text-align: center;
    color: #6b7280;
  }

  .icon { font-size: 48px; line-height: 1; }

  .title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #374151;
  }

  .desc {
    margin: 0;
    font-size: 14px;
    max-width: 360px;
    line-height: 1.6;
  }

  .cta {
    margin-top: 8px;
    padding: 10px 20px;
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s;
  }
  .cta:hover { background: #1d4ed8; }
</style>
