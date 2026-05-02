<script lang="ts">
  import { mockSqlGenerations } from '../lib/mock';
  import type { SqlGeneration } from '../lib/types';
  import { dataSources, selectedDataSource } from '../lib/stores';
  import EmptyDataSource from './shared/EmptyDataSource.svelte';

  let generations: SqlGeneration[] = mockSqlGenerations;
  let selected: SqlGeneration | null = null;
  let copiedId: string | null = null;

  function selectGen(g: SqlGeneration) {
    selected = g;
  }

  function fmtDate(iso: string) {
    return new Date(iso).toLocaleString('ko-KR', {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  function confColor(score: number) {
    if (score >= 0.9) return '#16a34a';
    if (score >= 0.7) return '#ca8a04';
    return '#dc2626';
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
      <h1>SQL 생성</h1>
      <p class="subtitle">자연어 질문에서 생성된 SQL 이력을 확인합니다.</p>
    </div>
    <div class="hint-box">
      💬 오른쪽 채팅에서 새 SQL을 생성해보세요.
    </div>
  </div>

  <div class="gen-layout">
    <!-- History list -->
    <div class="history-list">
      <div class="list-header">최근 생성 이력</div>
      {#each generations as gen}
        <button
          class="history-item"
          class:active={selected?.id === gen.id}
          on:click={() => selectGen(gen)}
        >
          <p class="history-query">{gen.user_query}</p>
          <div class="history-meta">
            <span class="conf-badge" style="color:{confColor(gen.confidence_score)}">
              {Math.round(gen.confidence_score * 100)}%
            </span>
            <span class="history-date">{fmtDate(gen.created_at)}</span>
          </div>
        </button>
      {/each}
    </div>

    <!-- Detail -->
    <div class="gen-detail">
      {#if selected}
        <div class="detail-section">
          <div class="section-label">질문</div>
          <p class="query-text">{selected.user_query}</p>
        </div>

        <div class="detail-section">
          <div class="section-label-row">
            <span class="section-label">생성된 SQL</span>
            <button class="copy-btn" on:click={() => copy(selected.generated_sql, selected.id)}>
              {copiedId === selected.id ? '복사됨 ✓' : '복사'}
            </button>
          </div>
          <pre class="sql-code">{selected.generated_sql}</pre>
        </div>

        <div class="detail-section">
          <div class="section-label">설명</div>
          <p class="explanation">{selected.explanation}</p>
        </div>

        <div class="detail-meta-row">
          <span>
            신뢰도:
            <strong style="color:{confColor(selected.confidence_score)}">
              {Math.round(selected.confidence_score * 100)}%
            </strong>
          </span>
          <span>생성일시: {fmtDate(selected.created_at)}</span>
        </div>
      {:else}
        <div class="empty-detail">
          <p>왼쪽에서 이력을 선택하거나 오른쪽 채팅에서 질문을 입력하세요.</p>
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

  .hint-box {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    color: #1d4ed8;
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
  .explanation {
    margin: 0;
    font-size: 13px;
    color: #4b5563;
    line-height: 1.6;
  }
  .detail-meta-row {
    display: flex;
    gap: 24px;
    font-size: 12px;
    color: #6b7280;
    border-top: 1px solid #f3f4f6;
    padding-top: 12px;
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
