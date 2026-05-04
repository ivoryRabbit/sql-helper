<script lang="ts">
  import { onMount } from 'svelte';
  import type {
    DashboardListItem, DashboardResponse, WidgetCreateRequest,
    AnalysisHistoryItem, AnalysisExecutionResponse,
  } from '../lib/types';
  import { dashboardApi, dataAnalysisApi, ApiError } from '../lib/api';
  import { dataSources, selectedDataSource } from '../lib/stores';
  import EmptyDataSource from './shared/EmptyDataSource.svelte';

  // ── List view ──────────────────────────────────────────────────────────
  let dashboards: DashboardListItem[] = [];
  let listLoading = false;
  let listError: string | null = null;

  // ── Detail view ───────────────────────────────────────────────────────
  let detail: DashboardResponse | null = null;
  let detailLoading = false;
  let detailError: string | null = null;
  let htmlContent: string | null = null;
  let showHtml = false;
  let shareUrl: string | null = null;
  let sharing = false;

  // ── Analysis data (for widget visualization) ──────────────────────────
  let analysisHistory: AnalysisHistoryItem[] = [];
  // Cache: analysis_id → full result
  const analysisCache = new Map<string, AnalysisExecutionResponse>();
  let widgetData: Record<string, AnalysisExecutionResponse> = {};

  // ── Create form ───────────────────────────────────────────────────────
  let showCreateForm = false;
  let createTitle = '';
  let createDescription = '';
  let createPublic = false;
  let createTags = '';
  let creating = false;
  let createError: string | null = null;

  // ── Add widget form ───────────────────────────────────────────────────
  let showWidgetForm = false;
  let widgetType: WidgetCreateRequest['widget_type'] = 'chart';
  let widgetTitle = '';
  let widgetAnalysisId = '';
  let addingWidget = false;
  let widgetError: string | null = null;

  // ── Delete ────────────────────────────────────────────────────────────
  let deleting = false;

  onMount(async () => {
    await Promise.all([loadDashboards(), loadAnalysisHistory()]);
  });

  async function loadAnalysisHistory() {
    try {
      analysisHistory = (await dataAnalysisApi.getHistory()).filter(h => h.status === 'completed');
    } catch {}
  }

  async function loadDashboards() {
    listLoading = true;
    listError = null;
    try {
      dashboards = await dashboardApi.list();
    } catch (e) {
      listError = e instanceof ApiError ? e.message : String(e);
    } finally {
      listLoading = false;
    }
  }

  async function openDashboard(id: string) {
    detailLoading = true;
    detailError = null;
    detail = null;
    htmlContent = null;
    showHtml = false;
    shareUrl = null;
    showWidgetForm = false;

    try {
      detail = await dashboardApi.get(id);
      await loadWidgetData(detail.widgets);
    } catch (e) {
      detailError = e instanceof ApiError ? e.message : String(e);
    } finally {
      detailLoading = false;
    }
  }

  async function loadWidgetData(widgets: DashboardResponse['widgets']) {
    const needed = widgets.filter(w => w.analysis_id && !analysisCache.has(w.analysis_id));
    await Promise.all(needed.map(async w => {
      try {
        const res = await dataAnalysisApi.getResult(w.analysis_id!);
        analysisCache.set(w.analysis_id!, res);
      } catch {}
    }));
    widgetData = Object.fromEntries(
      widgets
        .filter(w => w.analysis_id && analysisCache.has(w.analysis_id))
        .map(w => [w.id, analysisCache.get(w.analysis_id!)!])
    );
  }

  function backToList() {
    detail = null;
    detailError = null;
    htmlContent = null;
    showHtml = false;
    shareUrl = null;
  }

  async function createDashboard() {
    if (!createTitle.trim()) return;
    creating = true;
    createError = null;
    try {
      const tags = createTags.split(',').map(t => t.trim()).filter(Boolean);
      await dashboardApi.create({
        title: createTitle.trim(),
        description: createDescription.trim() || undefined,
        is_public: createPublic,
        tags: tags.length ? tags : undefined,
      });
      showCreateForm = false;
      createTitle = '';
      createDescription = '';
      createPublic = false;
      createTags = '';
      await loadDashboards();
    } catch (e) {
      createError = e instanceof ApiError ? e.message : String(e);
    } finally {
      creating = false;
    }
  }

  async function deleteDashboard() {
    if (!detail) return;
    if (!confirm(`"${detail.title}" 대시보드를 삭제하시겠습니까?`)) return;
    deleting = true;
    try {
      await dashboardApi.delete(detail.id);
      backToList();
      await loadDashboards();
    } catch (e) {
      detailError = e instanceof ApiError ? e.message : String(e);
    } finally {
      deleting = false;
    }
  }

  async function togglePublic() {
    if (!detail) return;
    try {
      const updated = await dashboardApi.update(detail.id, { is_public: !detail.is_public });
      detail = updated;
      await loadDashboards();
    } catch (e) {
      detailError = e instanceof ApiError ? e.message : String(e);
    }
  }

  async function loadHtml() {
    if (!detail) return;
    try {
      const res = await dashboardApi.getHtml(detail.id);
      htmlContent = res.html;
      showHtml = true;
    } catch (e) {
      detailError = e instanceof ApiError ? e.message : String(e);
    }
  }

  async function shareDashboard() {
    if (!detail) return;
    sharing = true;
    try {
      const res = await dashboardApi.share(detail.id);
      shareUrl = res.share_url;
    } catch (e) {
      detailError = e instanceof ApiError ? e.message : String(e);
    } finally {
      sharing = false;
    }
  }

  async function addWidget() {
    if (!detail || !widgetTitle.trim()) return;
    addingWidget = true;
    widgetError = null;
    try {
      const widget = await dashboardApi.addWidget(detail.id, {
        widget_type: widgetType,
        title: widgetTitle.trim(),
        width: 4,
        height: 3,
        analysis_id: widgetAnalysisId || null,
      });
      detail = { ...detail, widgets: [...detail.widgets, widget] };
      // Preload the analysis data for the new widget
      if (widgetAnalysisId) {
        await loadWidgetData(detail.widgets);
      }
      showWidgetForm = false;
      widgetTitle = '';
      widgetType = 'chart';
      widgetAnalysisId = '';
    } catch (e) {
      widgetError = e instanceof ApiError ? e.message : String(e);
    } finally {
      addingWidget = false;
    }
  }

  async function deleteWidget(widgetId: string) {
    if (!detail) return;
    try {
      await dashboardApi.deleteWidget(detail.id, widgetId);
      detail = { ...detail, widgets: detail.widgets.filter(w => w.id !== widgetId) };
      const { [widgetId]: _, ...rest } = widgetData;
      widgetData = rest;
    } catch (e) {
      detailError = e instanceof ApiError ? e.message : String(e);
    }
  }

  async function copyShareUrl() {
    if (shareUrl) await navigator.clipboard.writeText(shareUrl).catch(() => {});
  }

  function fmtDate(iso: string) {
    return new Date(iso).toLocaleDateString('ko-KR', {
      year: 'numeric', month: 'short', day: 'numeric',
    });
  }

  function sqlSnippet(sql: string, maxLen = 60) {
    const s = sql.replace(/\s+/g, ' ').trim();
    return s.length > maxLen ? s.slice(0, maxLen) + '…' : s;
  }

  function fmtVal(v: unknown): string {
    if (v == null) return '—';
    if (typeof v === 'number') return v.toLocaleString('ko-KR');
    return String(v);
  }

  // SVG bar chart from first two columns (label, value)
  function buildBarChart(data: AnalysisExecutionResponse): { label: string; value: number; pct: number }[] | null {
    const cols = data.columns;
    if (cols.length < 2 || data.data.length === 0) return null;
    const labelCol = cols[0].name;
    const valueCol = cols.find(c =>
      ['integer','bigint','numeric','real','double','float','int'].some(t => c.type.toLowerCase().includes(t))
    )?.name ?? cols[1].name;

    const rows = data.data.slice(0, 10).map(row => ({
      label: String(row[labelCol] ?? ''),
      value: Number(row[valueCol] ?? 0),
    }));
    const max = Math.max(...rows.map(r => r.value), 1);
    return rows.map(r => ({ ...r, pct: (r.value / max) * 100 }));
  }

  const WIDGET_ICONS: Record<string, string> = {
    chart: '📈', table: '📋', metric: '🔢', text: '📝',
  };
</script>

{#if $dataSources.length === 0}
  <EmptyDataSource reason="none" />
{:else if !$selectedDataSource}
  <EmptyDataSource reason="select" />
{:else}
<div class="page">

  {#if !detail && !detailLoading}
    <!-- ── List view ───────────────────────────────────────────────────── -->
    <div class="page-header">
      <div>
        <h1>대시보드</h1>
        <p class="subtitle">데이터 분석 결과로 대시보드를 만들고 관리합니다.</p>
      </div>
      <button class="btn-primary" on:click={() => showCreateForm = !showCreateForm}>
        {showCreateForm ? '취소' : '+ 새 대시보드'}
      </button>
    </div>

    {#if showCreateForm}
      <div class="create-form">
        <h3 class="form-title">새 대시보드 만들기</h3>
        <div class="form-row">
          <label class="form-label">제목 <span class="required">*</span></label>
          <input class="form-input" bind:value={createTitle} placeholder="대시보드 제목" />
        </div>
        <div class="form-row">
          <label class="form-label">설명</label>
          <input class="form-input" bind:value={createDescription} placeholder="선택 사항" />
        </div>
        <div class="form-row">
          <label class="form-label">태그 (쉼표 구분)</label>
          <input class="form-input" bind:value={createTags} placeholder="예: 매출, 고객, 분석" />
        </div>
        <div class="form-row form-row-inline">
          <label class="form-label">공개 여부</label>
          <input type="checkbox" bind:checked={createPublic} />
          <span class="checkbox-label">{createPublic ? '공개' : '비공개'}</span>
        </div>
        {#if createError}
          <div class="error-banner">{createError}</div>
        {/if}
        <button class="btn-primary" on:click={createDashboard} disabled={creating || !createTitle.trim()}>
          {creating ? '생성 중...' : '대시보드 만들기'}
        </button>
      </div>
    {/if}

    {#if listError}
      <div class="error-banner">{listError}</div>
    {/if}

    {#if listLoading}
      <div class="center-msg">로딩 중...</div>
    {:else if dashboards.length === 0}
      <div class="center-msg empty-msg">
        <p>대시보드가 없습니다.</p>
        <p>'새 대시보드' 버튼으로 첫 대시보드를 만들어보세요.</p>
      </div>
    {:else}
      <div class="dashboard-grid">
        {#each dashboards as db}
          <div
            class="db-card"
            on:click={() => openDashboard(db.id)}
            on:keydown={e => e.key === 'Enter' && openDashboard(db.id)}
            role="button"
            tabindex="0"
          >
            <div class="db-card-top">
              <h3 class="db-title">{db.title}</h3>
              {#if db.is_public}
                <span class="public-badge">공개</span>
              {:else}
                <span class="private-badge">비공개</span>
              {/if}
            </div>
            {#if db.description}
              <p class="db-desc">{db.description}</p>
            {/if}
            {#if db.tags && db.tags.length > 0}
              <div class="db-tags">
                {#each db.tags as tag}
                  <span class="tag">{tag}</span>
                {/each}
              </div>
            {/if}
            <div class="db-footer">
              <span class="db-layout">{db.layout}</span>
              <span class="db-date">{fmtDate(db.created_at)}</span>
            </div>
          </div>
        {/each}
      </div>
    {/if}

  {:else if detailLoading}
    <div class="center-msg">로딩 중...</div>

  {:else if detail}
    <!-- ── Detail view ─────────────────────────────────────────────────── -->
    <div class="detail-header">
      <button class="back-btn" on:click={backToList}>← 목록으로</button>
      <div class="detail-title-row">
        <h2>{detail.title}</h2>
        <div class="detail-actions">
          <button class="action-btn" on:click={togglePublic}>
            {detail.is_public ? '🔓 공개' : '🔒 비공개'}
          </button>
          <button class="action-btn" on:click={loadHtml}>HTML 미리보기</button>
          <button class="action-btn" on:click={shareDashboard} disabled={sharing}>
            {sharing ? '처리 중...' : '공유 링크'}
          </button>
          <button class="action-btn danger" on:click={deleteDashboard} disabled={deleting}>
            {deleting ? '삭제 중...' : '삭제'}
          </button>
        </div>
      </div>
      {#if detail.description}
        <p class="detail-desc">{detail.description}</p>
      {/if}
      {#if detail.tags && detail.tags.length > 0}
        <div class="db-tags">
          {#each detail.tags as tag}<span class="tag">{tag}</span>{/each}
        </div>
      {/if}
    </div>

    {#if detailError}
      <div class="error-banner">{detailError}</div>
    {/if}

    {#if shareUrl}
      <div class="share-box">
        <span class="share-label">공유 URL:</span>
        <code class="share-url">{shareUrl}</code>
        <button class="copy-btn" on:click={copyShareUrl}>복사</button>
      </div>
    {/if}

    {#if showHtml && htmlContent}
      <div class="html-preview-wrap">
        <div class="html-preview-header">
          <span>HTML 미리보기</span>
          <button class="close-btn" on:click={() => showHtml = false}>✕ 닫기</button>
        </div>
        <iframe
          srcdoc={htmlContent}
          title="Dashboard HTML preview"
          class="html-frame"
          sandbox="allow-scripts"
        ></iframe>
      </div>
    {/if}

    <!-- Widgets section -->
    <div class="widgets-section">
      <div class="widgets-header">
        <span class="widgets-title">위젯 ({detail.widgets.length})</span>
        <button class="btn-secondary" on:click={() => showWidgetForm = !showWidgetForm}>
          {showWidgetForm ? '취소' : '+ 위젯 추가'}
        </button>
      </div>

      {#if showWidgetForm}
        <div class="widget-form">
          <div class="form-row">
            <label class="form-label">위젯 유형</label>
            <select class="form-select" bind:value={widgetType}>
              <option value="chart">📈 차트</option>
              <option value="table">📋 테이블</option>
              <option value="metric">🔢 지표</option>
              <option value="text">📝 텍스트</option>
            </select>
          </div>
          <div class="form-row">
            <label class="form-label">위젯 제목</label>
            <input class="form-input" bind:value={widgetTitle} placeholder="위젯 제목" />
          </div>
          <div class="form-row">
            <label class="form-label">연결할 분석 결과</label>
            <select class="form-select full" bind:value={widgetAnalysisId}>
              <option value="">— 선택 안 함 —</option>
              {#each analysisHistory as h}
                <option value={h.id}>{sqlSnippet(h.executed_sql)} ({(h.row_count ?? 0).toLocaleString()} rows)</option>
              {/each}
            </select>
          </div>
          {#if widgetError}
            <div class="error-banner">{widgetError}</div>
          {/if}
          <button class="btn-primary small" on:click={addWidget}
            disabled={addingWidget || !widgetTitle.trim()}>
            {addingWidget ? '추가 중...' : '추가'}
          </button>
        </div>
      {/if}

      {#if detail.widgets.length === 0}
        <div class="empty-widgets">위젯이 없습니다. 위의 버튼으로 추가하세요.</div>
      {:else}
        <div class="widget-grid">
          {#each detail.widgets as widget}
            {@const wdata = widgetData[widget.id]}
            <div class="widget-card">
              <div class="widget-header">
                <span class="widget-icon">{WIDGET_ICONS[widget.widget_type] ?? '📦'}</span>
                <span class="widget-title">{widget.title}</span>
                <span class="widget-type">{widget.widget_type}</span>
                <button class="widget-delete" on:click={() => deleteWidget(widget.id)} title="삭제">✕</button>
              </div>

              {#if wdata}
                <div class="widget-source">{sqlSnippet(wdata.executed_sql)}</div>

                {#if widget.widget_type === 'table'}
                  <!-- Table widget: first 5 rows -->
                  <div class="widget-table-wrap">
                    <table class="widget-table">
                      <thead>
                        <tr>
                          {#each wdata.columns as col}
                            <th>{col.name}</th>
                          {/each}
                        </tr>
                      </thead>
                      <tbody>
                        {#each wdata.data.slice(0, 5) as row}
                          <tr>
                            {#each wdata.columns as col}
                              <td>{fmtVal(row[col.name])}</td>
                            {/each}
                          </tr>
                        {/each}
                      </tbody>
                    </table>
                    {#if wdata.data.length > 5}
                      <div class="widget-more">+{wdata.data.length - 5} rows more</div>
                    {/if}
                  </div>

                {:else if widget.widget_type === 'metric'}
                  <!-- Metric widget: key stats -->
                  <div class="metric-grid">
                    <div class="metric-item">
                      <span class="metric-label">행 수</span>
                      <span class="metric-value">{(wdata.row_count ?? wdata.data.length).toLocaleString()}</span>
                    </div>
                    <div class="metric-item">
                      <span class="metric-label">컬럼 수</span>
                      <span class="metric-value">{wdata.columns.length}</span>
                    </div>
                    {#each wdata.statistics.filter(s => s.avg_value != null).slice(0, 3) as stat}
                      <div class="metric-item">
                        <span class="metric-label">{stat.column_name} avg</span>
                        <span class="metric-value">{stat.avg_value != null ? stat.avg_value.toFixed(2) : '—'}</span>
                      </div>
                    {/each}
                  </div>

                {:else if widget.widget_type === 'chart'}
                  <!-- Chart widget: simple SVG bar chart -->
                  {@const bars = buildBarChart(wdata)}
                  {#if bars}
                    <div class="bar-chart">
                      {#each bars as bar}
                        <div class="bar-row">
                          <span class="bar-label" title={bar.label}>{bar.label}</span>
                          <div class="bar-track">
                            <div class="bar-fill" style="width:{bar.pct}%"></div>
                          </div>
                          <span class="bar-val">{bar.value.toLocaleString('ko-KR')}</span>
                        </div>
                      {/each}
                    </div>
                  {:else}
                    <div class="no-chart">차트를 그리기에 데이터가 부족합니다.</div>
                  {/if}
                {/if}

              {:else}
                <div class="no-data">분석 결과가 연결되지 않았습니다.</div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>

  {:else if detailError}
    <div class="page-header">
      <button class="back-btn" on:click={backToList}>← 목록으로</button>
    </div>
    <div class="error-banner">{detailError}</div>
  {/if}

</div>
{/if}

<style>
  .page { padding: 28px 32px; height: 100%; display: flex; flex-direction: column; overflow-y: auto; }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
    flex-shrink: 0;
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
  .btn-primary:hover:not(:disabled) { background: #1d4ed8; }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-primary.small { padding: 6px 14px; }

  .btn-secondary {
    padding: 6px 14px;
    background: #fff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    color: #374151;
  }
  .btn-secondary:hover { background: #f3f4f6; }

  /* Create form */
  .create-form {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 20px;
    background: #f9fafb;
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex-shrink: 0;
  }
  .form-title { margin: 0; font-size: 15px; font-weight: 600; }
  .form-row { display: flex; flex-direction: column; gap: 4px; }
  .form-row-inline { flex-direction: row; align-items: center; gap: 10px; }
  .form-label { font-size: 12px; font-weight: 600; color: #6b7280; }
  .required { color: #dc2626; }
  .form-input {
    padding: 8px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 13px;
    background: #fff;
  }
  .form-input:focus { outline: none; border-color: #3b82f6; }
  .checkbox-label { font-size: 13px; color: #374151; }

  .error-banner {
    padding: 10px 14px;
    background: #fee2e2;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    font-size: 13px;
    color: #dc2626;
    flex-shrink: 0;
  }

  /* Dashboard grid */
  .dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
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
  .db-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 10px; }
  .tag { font-size: 11px; padding: 2px 8px; background: #eff6ff; color: #1d4ed8; border-radius: 10px; }
  .db-footer { display: flex; justify-content: space-between; font-size: 12px; color: #9ca3af; }
  .db-layout { text-transform: capitalize; }

  /* Center/empty */
  .center-msg {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    font-size: 14px;
    color: #6b7280;
  }
  .empty-msg { flex-direction: column; gap: 4px; text-align: center; }
  .empty-msg p { margin: 0; }

  /* Detail */
  .detail-header { margin-bottom: 20px; flex-shrink: 0; }
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
  .detail-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 8px;
  }
  h2 { margin: 0; font-size: 20px; }
  .detail-actions { display: flex; gap: 8px; flex-wrap: wrap; }
  .action-btn {
    padding: 6px 14px;
    background: #fff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    color: #374151;
  }
  .action-btn:hover:not(:disabled) { background: #f3f4f6; }
  .action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .action-btn.danger { color: #dc2626; border-color: #fca5a5; }
  .action-btn.danger:hover:not(:disabled) { background: #fee2e2; }
  .detail-desc { margin: 4px 0 8px; font-size: 13px; color: #6b7280; }

  /* Share box */
  .share-box {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    margin-bottom: 12px;
    flex-shrink: 0;
    flex-wrap: wrap;
  }
  .share-label { font-size: 12px; font-weight: 600; color: #15803d; flex-shrink: 0; }
  .share-url { font-size: 12px; font-family: monospace; color: #374151; flex: 1; word-break: break-all; }
  .copy-btn {
    padding: 3px 10px;
    background: #fff;
    border: 1px solid #d1d5db;
    border-radius: 5px;
    font-size: 12px;
    cursor: pointer;
    flex-shrink: 0;
  }
  .copy-btn:hover { background: #f3f4f6; }

  /* HTML preview */
  .html-preview-wrap {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 20px;
    flex-shrink: 0;
  }
  .html-preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 14px;
    background: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
    font-size: 13px;
    font-weight: 500;
  }
  .close-btn {
    background: transparent;
    border: none;
    color: #6b7280;
    font-size: 12px;
    cursor: pointer;
  }
  .close-btn:hover { color: #111827; }
  .html-frame { width: 100%; height: 400px; border: none; background: #fff; }

  /* Widgets section */
  .widgets-section { flex: 1; display: flex; flex-direction: column; gap: 12px; }
  .widgets-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
  }
  .widgets-title { font-size: 14px; font-weight: 600; }

  /* Widget form */
  .widget-form {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 16px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    flex-shrink: 0;
  }
  .form-select {
    padding: 7px 10px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 13px;
    background: #fff;
    cursor: pointer;
  }
  .form-select.full { width: 100%; }

  /* Widget cards */
  .empty-widgets {
    padding: 24px;
    text-align: center;
    font-size: 13px;
    color: #9ca3af;
    border: 1px dashed #e5e7eb;
    border-radius: 8px;
  }
  .widget-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }
  .widget-card {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px;
    background: #fff;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .widget-header { display: flex; align-items: center; gap: 6px; }
  .widget-icon { font-size: 16px; flex-shrink: 0; }
  .widget-title { font-size: 13px; font-weight: 600; flex: 1; }
  .widget-type {
    font-size: 10px;
    padding: 1px 6px;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    color: #6b7280;
    text-transform: uppercase;
  }
  .widget-delete {
    background: transparent;
    border: none;
    color: #9ca3af;
    font-size: 12px;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 4px;
  }
  .widget-delete:hover { background: #fee2e2; color: #dc2626; }
  .widget-source {
    font-size: 11px;
    font-family: 'Cascadia Code', monospace;
    color: #6b7280;
    background: #f9fafb;
    padding: 4px 8px;
    border-radius: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .no-data { font-size: 12px; color: #9ca3af; text-align: center; padding: 12px 0; }
  .no-chart { font-size: 12px; color: #9ca3af; text-align: center; padding: 12px 0; }

  /* Table widget */
  .widget-table-wrap { overflow-x: auto; border: 1px solid #f3f4f6; border-radius: 6px; }
  .widget-table { width: 100%; border-collapse: collapse; font-size: 11px; }
  .widget-table th {
    padding: 5px 8px;
    background: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
    color: #6b7280;
    font-weight: 600;
    white-space: nowrap;
  }
  .widget-table td {
    padding: 4px 8px;
    border-bottom: 1px solid #f9fafb;
    white-space: nowrap;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .widget-more { font-size: 11px; color: #9ca3af; text-align: center; padding: 4px; }

  /* Metric widget */
  .metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .metric-item {
    background: #f9fafb;
    border: 1px solid #f3f4f6;
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .metric-label { font-size: 10px; color: #9ca3af; }
  .metric-value { font-size: 18px; font-weight: 700; color: #111827; font-variant-numeric: tabular-nums; }

  /* Bar chart widget */
  .bar-chart { display: flex; flex-direction: column; gap: 5px; }
  .bar-row { display: flex; align-items: center; gap: 6px; }
  .bar-label {
    font-size: 11px;
    color: #374151;
    width: 80px;
    flex-shrink: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .bar-track { flex: 1; height: 10px; background: #f3f4f6; border-radius: 3px; overflow: hidden; }
  .bar-fill { height: 100%; background: #2563eb; border-radius: 3px; transition: width 0.3s ease; }
  .bar-val { font-size: 10px; color: #6b7280; width: 60px; text-align: right; flex-shrink: 0; font-variant-numeric: tabular-nums; }
</style>
