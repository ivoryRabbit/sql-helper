<script lang="ts">
  import { onMount } from 'svelte';
  import type { DashboardListItem, DashboardResponse, WidgetCreateRequest } from '../lib/types';
  import { dashboardApi, ApiError } from '../lib/api';
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
  let addingWidget = false;
  let widgetError: string | null = null;

  // ── Delete ────────────────────────────────────────────────────────────
  let deleting = false;

  onMount(loadDashboards);

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
    } catch (e) {
      detailError = e instanceof ApiError ? e.message : String(e);
    } finally {
      detailLoading = false;
    }
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
      const res = await dashboardApi.create({
        title: createTitle.trim(),
        description: createDescription.trim() || undefined,
        is_public: createPublic,
        tags: tags.length ? tags : undefined,
      });
      dashboards = [{ ...res, widgets: undefined as never }, ...dashboards];
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
      });
      detail = { ...detail, widgets: [...detail.widgets, widget] };
      showWidgetForm = false;
      widgetTitle = '';
      widgetType = 'chart';
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
        <p class="subtitle">저장된 대시보드를 확인하고 관리합니다.</p>
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
        <p>위의 '새 대시보드' 버튼으로 첫 대시보드를 만들어보세요.</p>
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
          <select class="form-select" bind:value={widgetType}>
            <option value="chart">📈 차트</option>
            <option value="table">📋 테이블</option>
            <option value="metric">🔢 지표</option>
            <option value="text">📝 텍스트</option>
          </select>
          <input class="form-input" bind:value={widgetTitle} placeholder="위젯 제목" />
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
            <div class="widget-card">
              <div class="widget-header">
                <span class="widget-icon">{WIDGET_ICONS[widget.widget_type] ?? '📦'}</span>
                <span class="widget-title">{widget.title}</span>
                <span class="widget-type">{widget.widget_type}</span>
                <button class="widget-delete" on:click={() => deleteWidget(widget.id)} title="삭제">✕</button>
              </div>
              <div class="widget-meta">
                {widget.width}×{widget.height} &nbsp;|&nbsp;
                ({widget.position_x}, {widget.position_y})
                {#if widget.analysis_id}
                  &nbsp;| 분석 연결됨
                {/if}
              </div>
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
  .empty-msg {
    flex-direction: column;
    gap: 4px;
    text-align: center;
  }
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
  .html-frame {
    width: 100%;
    height: 400px;
    border: none;
    background: #fff;
  }

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
    gap: 8px;
    align-items: center;
    padding: 12px 14px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    flex-shrink: 0;
    flex-wrap: wrap;
  }
  .form-select {
    padding: 6px 10px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 13px;
    background: #fff;
    cursor: pointer;
  }

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
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 12px;
  }
  .widget-card {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 12px 14px;
    background: #fff;
    display: flex;
    flex-direction: column;
    gap: 6px;
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
  .widget-meta { font-size: 11px; color: #9ca3af; }
</style>
