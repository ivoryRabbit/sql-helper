<script lang="ts">
  import { mockDashboards } from '../lib/mock';
  import type { Dashboard, DashboardWidget } from '../lib/types';
  import { dataSources, selectedDataSource } from '../lib/stores';
  import EmptyDataSource from './shared/EmptyDataSource.svelte';

  let dashboards: Dashboard[] = mockDashboards;
  let selected: Dashboard | null = null;

  function selectDashboard(d: Dashboard) {
    selected = d;
  }

  function fmtDate(iso: string) {
    return new Date(iso).toLocaleDateString('ko-KR', {
      year: 'numeric', month: 'short', day: 'numeric',
    });
  }

  const WIDGET_ICONS: Record<string, string> = {
    chart: '📈',
    table: '📋',
    metric: '🔢',
    text: '📝',
  };

  const WIDGET_COLORS: Record<string, string> = {
    chart: '#eff6ff',
    table: '#f0fdf4',
    metric: '#fefce8',
    text: '#faf5ff',
  };
</script>

{#if $dataSources.length === 0}
  <EmptyDataSource reason="none" />
{:else if !$selectedDataSource}
  <EmptyDataSource reason="select" />
{:else}
<div class="page">
  <div class="page-header">
    <div>
      <h1>대시보드</h1>
      <p class="subtitle">저장된 대시보드를 확인하고 관리합니다.</p>
    </div>
    <button class="btn-primary" disabled title="백엔드 연동 예정">+ 새 대시보드</button>
  </div>

  {#if !selected}
    <!-- Dashboard grid -->
    <div class="dashboard-grid">
      {#each dashboards as db}
        <div class="db-card" on:click={() => selectDashboard(db)} role="button" tabindex="0"
          on:keydown={e => e.key === 'Enter' && selectDashboard(db)}>
          <div class="db-card-top">
            <h3 class="db-title">{db.title}</h3>
            {#if db.is_public}
              <span class="public-badge">공개</span>
            {:else}
              <span class="private-badge">비공개</span>
            {/if}
          </div>
          <p class="db-desc">{db.description}</p>
          <div class="db-tags">
            {#each db.tags as tag}
              <span class="tag">{tag}</span>
            {/each}
          </div>
          <div class="db-footer">
            <span class="widget-count">{db.widgets.length}개 위젯</span>
            <span class="db-date">{fmtDate(db.created_at)}</span>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <!-- Dashboard detail -->
    <div class="detail-header">
      <button class="back-btn" on:click={() => selected = null}>← 목록으로</button>
      <div>
        <h2 class="detail-title">{selected.title}</h2>
        <p class="detail-desc">{selected.description}</p>
      </div>
    </div>

    <div class="widget-grid">
      {#each selected.widgets as widget}
        <div
          class="widget-card"
          style="
            grid-column: span {Math.min(widget.width, 6)};
            background: {WIDGET_COLORS[widget.type]};
          "
        >
          <div class="widget-header">
            <span class="widget-icon">{WIDGET_ICONS[widget.type]}</span>
            <span class="widget-title">{widget.title}</span>
            <span class="widget-type">{widget.type}</span>
          </div>
          <div class="widget-placeholder">
            <span>위젯 미리보기<br/>(백엔드 연동 예정)</span>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
{/if}

<style>
  .page { padding: 28px 32px; max-width: 960px; }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
  }
  h1 { margin: 0 0 4px; font-size: 22px; }
  .subtitle { margin: 0; color: #6b7280; font-size: 14px; }

  .btn-primary {
    padding: 8px 18px;
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
  }
  .btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

  /* Dashboard grid */
  .dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }
  .db-card {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 18px;
    background: #fff;
    cursor: pointer;
    transition: box-shadow 0.15s, border-color 0.15s;
  }
  .db-card:hover { border-color: #2563eb; box-shadow: 0 2px 8px #2563eb20; }
  .db-card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 8px; }
  h3.db-title { margin: 0; font-size: 16px; font-weight: 600; }
  .public-badge { font-size: 11px; padding: 2px 8px; background: #dcfce7; color: #16a34a; border-radius: 10px; flex-shrink: 0; }
  .private-badge { font-size: 11px; padding: 2px 8px; background: #f3f4f6; color: #6b7280; border-radius: 10px; flex-shrink: 0; }
  .db-desc { margin: 0 0 10px; font-size: 13px; color: #6b7280; }
  .db-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }
  .tag { font-size: 11px; padding: 2px 8px; background: #eff6ff; color: #1d4ed8; border-radius: 10px; }
  .db-footer { display: flex; justify-content: space-between; font-size: 12px; color: #9ca3af; }
  .widget-count { font-weight: 500; }

  /* Detail */
  .detail-header { margin-bottom: 20px; }
  .back-btn {
    background: transparent;
    border: none;
    color: #2563eb;
    font-size: 13px;
    cursor: pointer;
    padding: 0;
    margin-bottom: 10px;
  }
  .back-btn:hover { text-decoration: underline; }
  h2.detail-title { margin: 0 0 4px; font-size: 20px; }
  .detail-desc { margin: 0; color: #6b7280; font-size: 13px; }

  .widget-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
  }
  .widget-card {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px;
    min-height: 140px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .widget-header { display: flex; align-items: center; gap: 6px; }
  .widget-icon { font-size: 16px; }
  .widget-title { font-size: 13px; font-weight: 600; flex: 1; }
  .widget-type {
    font-size: 10px;
    padding: 1px 6px;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    color: #6b7280;
    text-transform: uppercase;
  }
  .widget-placeholder {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: #9ca3af;
    text-align: center;
    border: 1px dashed #d1d5db;
    border-radius: 6px;
    padding: 12px;
    line-height: 1.6;
  }
</style>
