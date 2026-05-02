<script lang="ts">
  import { mockAnalysisResult } from '../lib/mock';
  import type { AnalysisResult, AnalysisColumn } from '../lib/types';
  import { dataSources, selectedDataSource } from '../lib/stores';
  import EmptyDataSource from './shared/EmptyDataSource.svelte';

  let result: AnalysisResult = mockAnalysisResult;
  let activeTab: 'data' | 'stats' = 'data';

  function fmtNum(v: unknown) {
    if (v == null) return '—';
    if (typeof v === 'number') return v.toLocaleString('ko-KR');
    return String(v);
  }

  function colType(col: AnalysisColumn) {
    if (col.type === 'date' || col.type === 'timestamptz') return 'date';
    if (['decimal', 'float', 'bigint', 'integer', 'int'].includes(col.type)) return 'number';
    return 'text';
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
      <h1>데이터 분석</h1>
      <p class="subtitle">SQL 실행 결과를 통계와 함께 분석합니다.</p>
    </div>
    <div class="exec-meta">
      <span class="meta-item">⏱ {result.execution_time_ms}ms</span>
      <span class="meta-item">📊 {result.row_count.toLocaleString()} rows</span>
      <span class="meta-item">{result.columns.length} columns</span>
    </div>
  </div>

  <!-- SQL preview -->
  <div class="sql-preview">
    <pre class="sql-code">{result.sql}</pre>
  </div>

  <!-- Tabs -->
  <div class="tabs">
    <button class="tab" class:active={activeTab === 'data'} on:click={() => activeTab = 'data'}>
      데이터 테이블
    </button>
    <button class="tab" class:active={activeTab === 'stats'} on:click={() => activeTab = 'stats'}>
      컬럼 통계
    </button>
  </div>

  {#if activeTab === 'data'}
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            {#each result.columns as col}
              <th class:num={colType(col) === 'number'}>{col.name}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each result.data as row}
            <tr>
              {#each result.columns as col}
                <td class:num={colType(col) === 'number'}>{fmtNum(row[col.name])}</td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <div class="stats-grid">
      {#each result.columns as col}
        <div class="stat-card">
          <div class="stat-name">{col.name}</div>
          <div class="stat-type">{col.type}</div>
          <div class="stat-rows">
            <div class="stat-row">
              <span>고유값</span>
              <strong>{col.unique_count.toLocaleString()}</strong>
            </div>
            <div class="stat-row">
              <span>Null</span>
              <strong>{col.null_count}</strong>
            </div>
            {#if col.min_value != null}
              <div class="stat-row">
                <span>최솟값</span>
                <strong>{fmtNum(col.min_value)}</strong>
              </div>
            {/if}
            {#if col.max_value != null}
              <div class="stat-row">
                <span>최댓값</span>
                <strong>{fmtNum(col.max_value)}</strong>
              </div>
            {/if}
            {#if col.avg_value != null}
              <div class="stat-row">
                <span>평균</span>
                <strong>{fmtNum(col.avg_value)}</strong>
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
{/if}

<style>
  .page { padding: 28px 32px; height: 100%; display: flex; flex-direction: column; }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
    flex-shrink: 0;
  }
  h1 { margin: 0 0 4px; font-size: 22px; }
  .subtitle { margin: 0; color: #6b7280; font-size: 14px; }

  .exec-meta { display: flex; gap: 12px; align-items: center; }
  .meta-item {
    font-size: 12px;
    padding: 4px 10px;
    background: #f3f4f6;
    border-radius: 6px;
    color: #374151;
  }

  .sql-preview {
    margin-bottom: 16px;
    flex-shrink: 0;
  }
  .sql-code {
    margin: 0;
    padding: 12px 16px;
    background: #0b1120;
    color: #93c5fd;
    font-size: 12px;
    font-family: 'Cascadia Code', monospace;
    border-radius: 8px;
    overflow-x: auto;
    white-space: pre;
  }

  .tabs {
    display: flex;
    gap: 4px;
    margin-bottom: 12px;
    flex-shrink: 0;
  }
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
  }
  .data-table th.num, .data-table td.num { text-align: right; }
  .data-table td {
    padding: 8px 14px;
    border-bottom: 1px solid #f3f4f6;
    font-variant-numeric: tabular-nums;
  }

  /* Stats */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
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
  .stat-type {
    font-size: 11px;
    color: #2563eb;
    margin-bottom: 10px;
    font-family: monospace;
  }
  .stat-rows { display: flex; flex-direction: column; gap: 6px; }
  .stat-row {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #6b7280;
  }
  .stat-row strong { color: #111827; font-variant-numeric: tabular-nums; }
</style>
