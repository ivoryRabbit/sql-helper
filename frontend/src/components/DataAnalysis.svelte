<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { AnalysisExecutionResponse, AnalysisHistoryItem } from '../lib/types';
  import { dataAnalysisApi, ApiError } from '../lib/api';
  import { dataSources, selectedDataSource, pendingSql } from '../lib/stores';
  import EmptyDataSource from './shared/EmptyDataSource.svelte';

  let sql = '';
  let executing = false;
  let result: AnalysisExecutionResponse | null = null;
  let execError: string | null = null;
  let activeTab: 'data' | 'stats' | 'insights' = 'data';

  let history: AnalysisHistoryItem[] = [];
  let historyLoading = false;

  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let exporting = false;
  let exportError: string | null = null;

  onMount(async () => {
    if ($pendingSql) {
      sql = $pendingSql;
      pendingSql.set(null);
    }
    await loadHistory();
  });

  onDestroy(() => {
    if (pollTimer) clearInterval(pollTimer);
  });

  async function loadHistory() {
    historyLoading = true;
    try {
      history = await dataAnalysisApi.getHistory();
    } catch {}
    finally {
      historyLoading = false;
    }
  }

  async function execute() {
    if (!$selectedDataSource || !sql.trim() || executing) return;
    executing = true;
    result = null;
    execError = null;
    exportError = null;
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }

    try {
      result = await dataAnalysisApi.execute({
        sql: sql.trim(),
        data_source_id: $selectedDataSource.id,
      });
      if (result.status === 'running') startPolling(result.id);
      await loadHistory();
    } catch (e) {
      execError = e instanceof ApiError ? e.message : String(e);
    } finally {
      executing = false;
    }
  }

  function startPolling(id: string) {
    pollTimer = setInterval(async () => {
      try {
        const updated = await dataAnalysisApi.getResult(id);
        result = updated;
        if (updated.status !== 'running') {
          clearInterval(pollTimer!);
          pollTimer = null;
        }
      } catch {
        clearInterval(pollTimer!);
        pollTimer = null;
      }
    }, 2000);
  }

  async function loadFromHistory(item: AnalysisHistoryItem) {
    execError = null;
    exportError = null;
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    try {
      result = await dataAnalysisApi.getResult(item.id);
      sql = item.executed_sql;
      activeTab = 'data';
      if (result.status === 'running') startPolling(result.id);
    } catch (e) {
      execError = e instanceof ApiError ? e.message : String(e);
    }
  }

  async function doExport(format: 'csv' | 'json') {
    if (!result) return;
    exporting = true;
    exportError = null;
    try {
      const res = await dataAnalysisApi.exportResults({ analysis_id: result.id, format });
      window.open(res.download_url, '_blank');
    } catch (e) {
      exportError = e instanceof ApiError ? e.message : String(e);
    } finally {
      exporting = false;
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      execute();
    }
  }

  function fmtVal(v: unknown): string {
    if (v == null) return '—';
    if (typeof v === 'number') return v.toLocaleString('ko-KR');
    return String(v);
  }

  function fmtTime(iso: string): string {
    return new Date(iso).toLocaleString('ko-KR', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  }

  function statusColor(status: string): string {
    if (status === 'completed') return '#16a34a';
    if (status === 'failed') return '#dc2626';
    return '#ca8a04';
  }

  $: isRunning = result?.status === 'running';
</script>

{#if $dataSources.length === 0}
  <EmptyDataSource reason="none" />
{:else if !$selectedDataSource}
  <EmptyDataSource reason="select" />
{:else}
<div class="page">
  <div class="page-header">
    <div>
      <h1>데이터 분석</h1>
      <p class="subtitle">SQL을 실행하고 결과를 통계와 함께 분석합니다.</p>
    </div>
  </div>

  <div class="analysis-layout">
    <!-- Left: execution history -->
    <div class="history-panel">
      <div class="panel-header">실행 이력 ({history.length})</div>
      {#if historyLoading}
        <div class="panel-empty">로딩 중...</div>
      {:else if history.length === 0}
        <div class="panel-empty">아직 실행 이력이 없습니다.</div>
      {:else}
        {#each history as item}
          <button
            class="history-item"
            class:active={result?.id === item.id}
            on:click={() => loadFromHistory(item)}
          >
            <div class="item-sql">{item.executed_sql.replace(/\s+/g, ' ').trim().slice(0, 70)}</div>
            <div class="item-meta">
              <span class="item-status" style="color:{statusColor(item.status)}">{item.status}</span>
              {#if item.row_count != null}
                <span>{item.row_count.toLocaleString()} rows</span>
              {/if}
              <span>{fmtTime(item.created_at)}</span>
            </div>
          </button>
        {/each}
      {/if}
    </div>

    <!-- Right: editor + results -->
    <div class="main-panel">
      <!-- SQL editor -->
      <div class="editor-section">
        <textarea
          bind:value={sql}
          placeholder="SELECT * FROM schema.table LIMIT 100&#10;&#10;⌘+Enter 또는 Ctrl+Enter로 실행"
          class="sql-input"
          on:keydown={handleKeyDown}
          spellcheck="false"
        ></textarea>
        <button
          class="run-btn"
          on:click={execute}
          disabled={executing || !sql.trim() || isRunning}
        >
          {executing ? '실행 중...' : '▶ 실행'}
        </button>
      </div>

      {#if execError}
        <div class="error-banner">{execError}</div>
      {/if}

      {#if result}
        <!-- Result meta bar -->
        <div class="result-meta">
          <span class="status-pill" style="color:{statusColor(result.status)};border-color:{statusColor(result.status)}">
            {result.status}
          </span>
          {#if result.execution_time_ms != null}
            <span class="meta-chip">⏱ {result.execution_time_ms.toLocaleString()}ms</span>
          {/if}
          {#if result.row_count != null}
            <span class="meta-chip">📊 {result.row_count.toLocaleString()} rows</span>
          {/if}
          {#if result.columns.length > 0}
            <span class="meta-chip">{result.columns.length} columns</span>
          {/if}

          {#if result.status === 'completed'}
            <div class="export-row">
              <button class="export-btn" on:click={() => doExport('csv')} disabled={exporting}>
                CSV 내보내기
              </button>
              <button class="export-btn" on:click={() => doExport('json')} disabled={exporting}>
                JSON 내보내기
              </button>
            </div>
          {/if}
        </div>

        {#if exportError}
          <div class="error-banner">{exportError}</div>
        {/if}

        {#if isRunning}
          <div class="running-notice">
            <span class="spinner"></span>
            분석 실행 중입니다. 완료되면 자동으로 결과가 표시됩니다...
          </div>
        {:else if result.status === 'failed'}
          <div class="error-banner">{result.error_message ?? '실행 중 오류가 발생했습니다.'}</div>
        {:else if result.status === 'completed'}
          <!-- Tabs -->
          <div class="tabs">
            <button class="tab" class:active={activeTab === 'data'} on:click={() => activeTab = 'data'}>
              데이터 테이블
            </button>
            <button class="tab" class:active={activeTab === 'stats'} on:click={() => activeTab = 'stats'}>
              컬럼 통계 ({result.statistics.length})
            </button>
            <button class="tab" class:active={activeTab === 'insights'} on:click={() => activeTab = 'insights'}>
              인사이트 ({result.insights.length})
            </button>
          </div>

          {#if activeTab === 'data'}
            {#if result.data.length === 0}
              <div class="empty-result">결과가 없습니다.</div>
            {:else}
              <div class="table-wrap">
                <table class="data-table">
                  <thead>
                    <tr>
                      {#each result.columns as col}
                        <th title={col.type}>{col.name}</th>
                      {/each}
                    </tr>
                  </thead>
                  <tbody>
                    {#each result.data as row}
                      <tr>
                        {#each result.columns as col}
                          <td>{fmtVal(row[col.name])}</td>
                        {/each}
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            {/if}

          {:else if activeTab === 'stats'}
            {#if result.statistics.length === 0}
              <div class="empty-result">통계 데이터가 없습니다.</div>
            {:else}
              <div class="stats-grid">
                {#each result.statistics as stat}
                  <div class="stat-card">
                    <div class="stat-name">{stat.column_name}</div>
                    <div class="stat-type">{stat.data_type}</div>
                    <div class="stat-rows">
                      <div class="stat-row"><span>전체</span><strong>{stat.total_count.toLocaleString()}</strong></div>
                      <div class="stat-row"><span>고유값</span><strong>{stat.unique_count.toLocaleString()}</strong></div>
                      <div class="stat-row"><span>Null</span><strong>{stat.null_count}</strong></div>
                      {#if stat.min_value != null}
                        <div class="stat-row"><span>최솟값</span><strong>{stat.min_value}</strong></div>
                      {/if}
                      {#if stat.max_value != null}
                        <div class="stat-row"><span>최댓값</span><strong>{stat.max_value}</strong></div>
                      {/if}
                      {#if stat.avg_value != null}
                        <div class="stat-row"><span>평균</span><strong>{stat.avg_value.toFixed(2)}</strong></div>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>
            {/if}

          {:else if activeTab === 'insights'}
            {#if result.insights.length === 0}
              <div class="empty-result">인사이트가 없습니다.</div>
            {:else}
              <div class="insights-list">
                {#each result.insights as insight}
                  <div class="insight-card">
                    <div class="insight-header">
                      <span class="insight-type">{insight.insight_type}</span>
                      {#if insight.confidence_score != null}
                        <span class="insight-conf">{Math.round(insight.confidence_score * 100)}%</span>
                      {/if}
                    </div>
                    <p class="insight-text">{insight.insight_text}</p>
                  </div>
                {/each}
              </div>
            {/if}
          {/if}
        {/if}
      {:else if !executing}
        <div class="empty-result">
          SQL을 입력하고 실행 버튼을 클릭하거나 <kbd>⌘ Enter</kbd>를 눌러 분석을 시작하세요.
        </div>
      {/if}
    </div>
  </div>
</div>
{/if}

<style>
  .page { padding: 28px 32px; height: 100%; display: flex; flex-direction: column; overflow: hidden; }

  .page-header { margin-bottom: 16px; flex-shrink: 0; }
  h1 { margin: 0 0 4px; font-size: 22px; }
  .subtitle { margin: 0; color: #6b7280; font-size: 14px; }

  .analysis-layout {
    display: flex;
    gap: 16px;
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  /* History panel */
  .history-panel {
    width: 240px;
    min-width: 240px;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    background: #fff;
    display: flex;
    flex-direction: column;
  }
  .panel-header {
    padding: 12px 14px;
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
    border-bottom: 1px solid #f3f4f6;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    flex-shrink: 0;
  }
  .panel-empty {
    padding: 20px 14px;
    font-size: 13px;
    color: #9ca3af;
    text-align: center;
  }
  .history-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    width: 100%;
    text-align: left;
    padding: 10px 14px;
    border: none;
    border-bottom: 1px solid #f3f4f6;
    background: transparent;
    cursor: pointer;
  }
  .history-item:hover { background: #f9fafb; }
  .history-item.active { background: #eff6ff; }
  .item-sql {
    font-size: 11px;
    font-family: 'Cascadia Code', monospace;
    color: #374151;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .item-meta { display: flex; gap: 6px; font-size: 10px; color: #9ca3af; flex-wrap: wrap; }
  .item-status { font-weight: 600; }

  /* Main panel */
  .main-panel {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 12px;
    overflow: hidden;
  }

  /* Editor */
  .editor-section { display: flex; gap: 10px; flex-shrink: 0; }
  .sql-input {
    flex: 1;
    min-height: 100px;
    max-height: 200px;
    padding: 12px 14px;
    background: #0b1120;
    color: #93c5fd;
    font-family: 'Cascadia Code', 'Fira Code', monospace;
    font-size: 13px;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    resize: vertical;
    line-height: 1.6;
  }
  .sql-input:focus { outline: none; border-color: #3b82f6; }
  .run-btn {
    padding: 0 20px;
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    align-self: flex-start;
    height: 40px;
  }
  .run-btn:hover:not(:disabled) { background: #1d4ed8; }
  .run-btn:disabled { opacity: 0.5; cursor: not-allowed; }

  /* Error */
  .error-banner {
    padding: 10px 14px;
    background: #fee2e2;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    font-size: 13px;
    color: #dc2626;
    flex-shrink: 0;
  }

  /* Result meta */
  .result-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    flex-shrink: 0;
  }
  .status-pill {
    padding: 3px 10px;
    border: 1px solid currentColor;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 600;
  }
  .meta-chip {
    padding: 3px 10px;
    background: #f3f4f6;
    border-radius: 6px;
    font-size: 12px;
    color: #374151;
  }
  .export-row { display: flex; gap: 6px; margin-left: auto; }
  .export-btn {
    padding: 4px 12px;
    background: #fff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    color: #374151;
  }
  .export-btn:hover:not(:disabled) { background: #f3f4f6; }
  .export-btn:disabled { opacity: 0.5; }

  /* Running notice */
  .running-notice {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 16px;
    background: #fefce8;
    border: 1px solid #fde047;
    border-radius: 8px;
    font-size: 13px;
    color: #713f12;
    flex-shrink: 0;
  }
  .spinner {
    width: 16px; height: 16px;
    border: 2px solid #fde047;
    border-top-color: #ca8a04;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    flex-shrink: 0;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Tabs */
  .tabs { display: flex; gap: 4px; flex-shrink: 0; }
  .tab {
    padding: 7px 16px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background: #fff;
    font-size: 13px;
    cursor: pointer;
    color: #6b7280;
  }
  .tab.active { background: #2563eb; border-color: #2563eb; color: #fff; font-weight: 600; }
  .tab:hover:not(.active) { background: #f9fafb; }

  /* Data table */
  .table-wrap { flex: 1; overflow: auto; border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; }
  .data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .data-table th {
    padding: 10px 14px;
    border-bottom: 2px solid #e5e7eb;
    text-align: left;
    color: #6b7280;
    font-size: 12px;
    font-weight: 600;
    background: #f9fafb;
    position: sticky;
    top: 0;
    white-space: nowrap;
  }
  .data-table td {
    padding: 7px 14px;
    border-bottom: 1px solid #f3f4f6;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* Stats grid */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
    gap: 12px;
    overflow-y: auto;
    flex: 1;
  }
  .stat-card {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 16px;
    background: #fff;
  }
  .stat-name { font-weight: 600; font-size: 14px; margin-bottom: 2px; font-family: monospace; }
  .stat-type { font-size: 11px; color: #2563eb; margin-bottom: 10px; font-family: monospace; }
  .stat-rows { display: flex; flex-direction: column; gap: 5px; }
  .stat-row { display: flex; justify-content: space-between; font-size: 12px; color: #6b7280; }
  .stat-row strong { color: #111827; font-variant-numeric: tabular-nums; }

  /* Insights */
  .insights-list { display: flex; flex-direction: column; gap: 10px; overflow-y: auto; flex: 1; }
  .insight-card {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 16px;
    background: #fff;
  }
  .insight-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .insight-type {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #2563eb;
    background: #eff6ff;
    padding: 2px 8px;
    border-radius: 10px;
  }
  .insight-conf { font-size: 12px; color: #6b7280; }
  .insight-text { margin: 0; font-size: 13px; color: #374151; line-height: 1.6; }

  /* Empty / placeholder */
  .empty-result {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #9ca3af;
    font-size: 14px;
    text-align: center;
    border: 1px dashed #e5e7eb;
    border-radius: 10px;
    padding: 32px;
  }
  kbd {
    display: inline-block;
    padding: 1px 6px;
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-family: monospace;
    font-size: 12px;
    color: #374151;
  }
</style>
