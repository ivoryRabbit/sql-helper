<script lang="ts">
  import { onMount } from 'svelte';
  import type { SqlGenerationHistoryItem } from '../lib/types';
  import { sqlAssistantApi, ApiError } from '../lib/api';
  import { dataSources, selectedDataSource } from '../lib/stores';
  import { language, t } from '../lib/i18n';
  import EmptyDataSource from './shared/EmptyDataSource.svelte';

  let generations: SqlGenerationHistoryItem[] = [];
  let loading = false;
  let loadError: string | null = null;
  let selected: SqlGenerationHistoryItem | null = null;
  let copiedId: string | null = null;

  $: dateLocale = $language === 'ko' ? 'ko-KR' : 'en-US';
  $: fmtDate = (iso: string) =>
    new Date(iso).toLocaleString(dateLocale, {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });

  onMount(loadHistory);

  async function loadHistory() {
    loading = true;
    loadError = null;
    try {
      generations = await sqlAssistantApi.getHistory();
    } catch (e) {
      loadError = e instanceof ApiError ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  function confColor(score: number | null) {
    if (score == null) return '#9ca3af';
    if (score >= 0.9) return '#16a34a';
    if (score >= 0.7) return '#ca8a04';
    return '#dc2626';
  }

  function validationBadgeStyle(status: string) {
    if (status === 'valid') return 'background:#dcfce7;color:#15803d';
    if (status === 'invalid') return 'background:#fee2e2;color:#dc2626';
    return 'background:#f3f4f6;color:#6b7280';
  }

  async function copy(sql: string, id: string) {
    await navigator.clipboard.writeText(sql).catch(() => {});
    copiedId = id;
    setTimeout(() => { copiedId = null; }, 1500);
  }
</script>

{#if $dataSources.length === 0}
  <EmptyDataSource reason="none" />
{:else if !$selectedDataSource}
  <EmptyDataSource reason="select" />
{:else}
<div class="page">
  <div class="page-header">
    <div>
      <h1>{$t('sql.title')}</h1>
      <p class="subtitle">{$t('sql.subtitle')}</p>
    </div>
    <div class="header-right">
      <button class="refresh-btn" on:click={loadHistory} disabled={loading}>
        {loading ? $t('common.loading') : $t('common.refresh')}
      </button>
      <div class="hint-box">{$t('sql.hint')}</div>
    </div>
  </div>

  {#if loadError}
    <div class="error-banner">{loadError}</div>
  {/if}

  <div class="gen-layout">
    <!-- History list -->
    <div class="history-list">
      <div class="list-header">{$t('sql.history.header', { count: generations.length })}</div>
      {#if loading}
        <div class="list-loading">{$t('sql.history.loading')}</div>
      {:else if generations.length === 0}
        <div class="list-empty">{$t('sql.history.empty')}</div>
      {:else}
        {#each generations as gen}
          <button
            class="history-item"
            class:active={selected?.id === gen.id}
            on:click={() => selected = gen}
          >
            <p class="history-query">{gen.user_query}</p>
            <div class="history-meta">
              {#if gen.confidence_score != null}
                <span class="conf-badge" style="color:{confColor(gen.confidence_score)}">
                  {Math.round(gen.confidence_score * 100)}%
                </span>
              {/if}
              <span class="history-date">{fmtDate(gen.created_at)}</span>
            </div>
          </button>
        {/each}
      {/if}
    </div>

    <!-- Detail -->
    <div class="gen-detail">
      {#if selected}
        <div class="detail-section">
          <div class="section-label">{$t('sql.detail.question')}</div>
          <p class="query-text">{selected.user_query}</p>
        </div>

        {#if selected.generated_sql}
          <div class="detail-section">
            <div class="section-label-row">
              <span class="section-label">{$t('sql.detail.generatedSql')}</span>
              <button class="copy-btn" on:click={() => selected && selected.generated_sql && copy(selected.generated_sql, selected.id)}>
                {copiedId === selected.id ? $t('sql.detail.copied') : $t('sql.detail.copy')}
              </button>
            </div>
            <pre class="sql-code">{selected.generated_sql}</pre>
          </div>
        {:else}
          <div class="detail-section">
            <div class="section-label">{$t('sql.detail.generatedSql')}</div>
            <p class="no-sql">{$t('sql.detail.noSql')}</p>
          </div>
        {/if}

        <div class="detail-meta-row">
          {#if selected.confidence_score != null}
            <span>
              {$t('sql.detail.confidence')}
              <strong style="color:{confColor(selected.confidence_score)}">
                {Math.round(selected.confidence_score * 100)}%
              </strong>
            </span>
          {/if}
          <span>
            {$t('sql.detail.validation')}
            <span class="validation-badge" style={validationBadgeStyle(selected.validation_status)}>
              {selected.validation_status}
            </span>
          </span>
          {#if selected.llm_model}
            <span>{$t('sql.detail.model')} <strong>{selected.llm_model}</strong></span>
          {/if}
          <span>{$t('sql.detail.createdAt')} {fmtDate(selected.created_at)}</span>
        </div>
      {:else}
        <div class="empty-detail">
          <p>{$t('sql.empty')}</p>
        </div>
      {/if}
    </div>
  </div>
</div>
{/if}

<style>
  .page { padding: 28px 32px; height: 100%; display: flex; flex-direction: column; }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
    flex-shrink: 0;
  }
  h1 { margin: 0 0 4px; font-size: 22px; }
  .subtitle { margin: 0; color: #6b7280; font-size: 14px; }

  .header-right { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
  .refresh-btn {
    padding: 6px 14px;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    color: #374151;
  }
  .refresh-btn:hover:not(:disabled) { background: #e5e7eb; }
  .refresh-btn:disabled { opacity: 0.5; cursor: default; }

  .hint-box {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
    color: #1d4ed8;
  }

  .error-banner {
    margin-bottom: 12px;
    padding: 10px 14px;
    background: #fee2e2;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    font-size: 13px;
    color: #dc2626;
    flex-shrink: 0;
  }

  .gen-layout {
    display: flex;
    gap: 16px;
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  /* History */
  .history-list {
    width: 260px;
    min-width: 260px;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    background: #fff;
  }
  .list-header {
    padding: 12px 14px;
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
    border-bottom: 1px solid #f3f4f6;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .list-loading, .list-empty {
    padding: 20px 14px;
    font-size: 13px;
    color: #9ca3af;
    text-align: center;
    line-height: 1.6;
    white-space: pre-line;
  }
  .history-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
    width: 100%;
    text-align: left;
    padding: 12px 14px;
    border: none;
    border-bottom: 1px solid #f3f4f6;
    background: transparent;
    cursor: pointer;
  }
  .history-item:hover { background: #f9fafb; }
  .history-item.active { background: #eff6ff; }
  .history-query { margin: 0; font-size: 13px; font-weight: 500; color: #111827; }
  .history-meta { display: flex; justify-content: space-between; align-items: center; }
  .conf-badge { font-size: 12px; font-weight: 600; }
  .history-date { font-size: 11px; color: #9ca3af; }

  /* Detail */
  .gen-detail {
    flex: 1;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    background: #fff;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .detail-section { display: flex; flex-direction: column; gap: 6px; }
  .section-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #9ca3af;
  }
  .section-label-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .query-text {
    margin: 0;
    font-size: 15px;
    font-weight: 500;
    color: #111827;
  }
  .sql-code {
    margin: 0;
    padding: 14px;
    background: #0b1120;
    color: #93c5fd;
    font-size: 13px;
    font-family: 'Cascadia Code', 'Fira Code', monospace;
    border-radius: 8px;
    overflow-x: auto;
    white-space: pre;
  }
  .no-sql { margin: 0; font-size: 13px; color: #9ca3af; font-style: italic; }
  .copy-btn {
    background: transparent;
    border: 1px solid #d1d5db;
    color: #374151;
    font-size: 12px;
    padding: 3px 10px;
    border-radius: 5px;
    cursor: pointer;
  }
  .copy-btn:hover { background: #f3f4f6; }
  .detail-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    font-size: 12px;
    color: #6b7280;
    border-top: 1px solid #f3f4f6;
    padding-top: 12px;
    margin-top: auto;
  }
  .validation-badge {
    display: inline-block;
    padding: 1px 7px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 500;
  }

  .empty-detail {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    color: #9ca3af;
    font-size: 14px;
    text-align: center;
  }
</style>
