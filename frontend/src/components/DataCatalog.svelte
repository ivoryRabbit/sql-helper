<script lang="ts">
  import { onMount } from 'svelte';
  import { dataCatalogApi, ApiError } from '../lib/api';
  import type { ApiTable, ApiTableDetail, ApiSchema, SemanticSearchResultItem } from '../lib/types';
  import { dataSources, selectedDataSource } from '../lib/stores';
  import EmptyDataSource from './shared/EmptyDataSource.svelte';

  // ── Shared ────────────────────────────────────────────────────────────────
  let mode: 'browse' | 'search' = 'browse';

  // ── Browse mode ───────────────────────────────────────────────────────────
  let schemas: ApiSchema[] = [];
  let tables: ApiTable[] = [];
  let selectedTable: ApiTableDetail | null = null;
  let selectedTableId: string | null = null;
  let browseSearch = '';
  let browseLoading = false;
  let browseError = '';
  let detailLoading = false;
  let detailError = '';

  // Refresh state
  let refreshing = false;
  let refreshMsg = '';
  let refreshOk = false;

  // Group tables by schema for tree display
  $: schemaGroups = schemas.map(s => ({
    schema: s,
    tables: tables.filter(t => t.schema_id === s.id && (
      !browseSearch ||
      t.table_name.toLowerCase().includes(browseSearch.toLowerCase()) ||
      (t.user_description ?? t.source_description ?? '').toLowerCase().includes(browseSearch.toLowerCase()) ||
      (t.tags ?? []).some(tag => tag.toLowerCase().includes(browseSearch.toLowerCase()))
    )),
  })).filter(g => g.tables.length > 0);

  function fmtRows(n: number) {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
    return String(n);
  }

  function tableDesc(t: ApiTable) {
    return t.user_description ?? t.source_description ?? '';
  }

  async function loadCatalog(dataSourceId: string) {
    browseLoading = true;
    browseError = '';
    schemas = [];
    tables = [];
    selectedTable = null;
    selectedTableId = null;
    try {
      const res = await dataCatalogApi.getSourceCatalog(dataSourceId);
      schemas = res.schemas;
      tables = res.tables;
    } catch (e) {
      browseError = e instanceof ApiError ? e.message : String(e);
    } finally {
      browseLoading = false;
    }
  }

  async function selectTable(table: ApiTable) {
    if (selectedTableId === table.id) return;
    selectedTableId = table.id;
    selectedTable = null;
    detailLoading = true;
    detailError = '';
    try {
      selectedTable = await dataCatalogApi.getTableDetail(table.id);
    } catch (e) {
      detailError = e instanceof ApiError ? e.message : String(e);
    } finally {
      detailLoading = false;
    }
  }

  async function triggerRefresh() {
    if (!$selectedDataSource || refreshing) return;
    refreshing = true;
    refreshMsg = '';
    try {
      const res = await dataCatalogApi.refresh($selectedDataSource.id);
      refreshOk = true;
      refreshMsg = `${res.message} (스키마 ${res.schemas_synced}, 테이블 ${res.tables_synced}, 컬럼 ${res.columns_synced})`;
      await loadCatalog($selectedDataSource.id);
    } catch (e) {
      refreshOk = false;
      refreshMsg = e instanceof ApiError ? e.message : String(e);
    } finally {
      refreshing = false;
    }
  }

  // Reload when the selected data source changes
  $: if ($selectedDataSource) {
    loadCatalog($selectedDataSource.id);
  }

  // ── Search mode ───────────────────────────────────────────────────────────
  let query = '';
  let searchResults: SemanticSearchResultItem[] = [];
  let searching = false;
  let searched = false;
  let searchError = '';
  let searchTimeMs = 0;

  const DOC_TYPE_COLOR: Record<string, string> = {
    table: '#2563eb',
    column: '#9333ea',
  };
  const TYPE_LABEL: Record<string, string> = {
    table: '테이블',
    column: '컬럼',
  };

  async function runSearch() {
    if (!query.trim() || !$selectedDataSource) return;
    searching = true;
    searched = false;
    searchError = '';
    searchResults = [];
    try {
      const res = await dataCatalogApi.semanticSearch({
        query: query.trim(),
        data_source_ids: [$selectedDataSource.id],
        search_type: 'both',
        limit: 20,
      });
      searchResults = res.results;
      searchTimeMs = res.search_time_ms;
      searched = true;
    } catch (e) {
      searchError = e instanceof ApiError ? e.message : String(e);
      searched = true;
    } finally {
      searching = false;
    }
  }

  function onSearchKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') runSearch();
  }

  function scorePct(score: number) {
    return Math.round(score * 100);
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
      <h1>데이터 카탈로그</h1>
      <p class="subtitle">스키마를 탐색하거나 자연어로 관련 테이블을 검색합니다.</p>
    </div>
    <div class="header-right">
      <div class="mode-tabs" role="tablist">
        <button
          class="mode-tab"
          class:active={mode === 'browse'}
          role="tab"
          aria-selected={mode === 'browse'}
          on:click={() => (mode = 'browse')}
        >
          📚 Browse
        </button>
        <button
          class="mode-tab"
          class:active={mode === 'search'}
          role="tab"
          aria-selected={mode === 'search'}
          on:click={() => (mode = 'search')}
        >
          🔍 Search
        </button>
      </div>
      {#if mode === 'browse'}
        <button class="btn-refresh" on:click={triggerRefresh} disabled={refreshing}>
          {refreshing ? '동기화 중…' : '카탈로그 동기화'}
        </button>
      {/if}
    </div>
  </div>

  {#if refreshMsg}
    <div class="banner" class:ok={refreshOk} class:fail={!refreshOk}>
      {refreshOk ? '✓ ' : '✗ '}{refreshMsg}
    </div>
  {/if}

  <!-- ── Browse mode ── -->
  {#if mode === 'browse'}
    <div class="browse-toolbar">
      <input class="browse-search" bind:value={browseSearch} placeholder="테이블·설명·태그 필터…" />
    </div>

    {#if browseLoading}
      <div class="loading">카탈로그 로딩 중…</div>
    {:else if browseError}
      <div class="banner fail">✗ {browseError}
        <button on:click={() => $selectedDataSource && loadCatalog($selectedDataSource.id)}>재시도</button>
      </div>
    {:else if schemas.length === 0}
      <div class="empty-catalog">
        <p>카탈로그 데이터가 없습니다.</p>
        <p class="hint">"카탈로그 동기화" 버튼을 눌러 스키마를 가져오세요.</p>
        <button class="btn-primary" on:click={triggerRefresh} disabled={refreshing}>
          {refreshing ? '동기화 중…' : '카탈로그 동기화'}
        </button>
      </div>
    {:else}
      <div class="catalog-layout">
        <div class="table-list">
          {#each schemaGroups as group}
            <div class="schema-group">
              <div class="schema-label">{group.schema.schema_name} <span class="table-cnt">{group.tables.length}</span></div>
              {#each group.tables as table}
                <button
                  class="table-item"
                  class:active={selectedTableId === table.id}
                  on:click={() => selectTable(table)}
                >
                  <div class="table-item-top">
                    <span class="table-name">{table.table_name}</span>
                    <span class="table-type" class:view={table.table_type === 'view'}>{table.table_type}</span>
                  </div>
                  <div class="table-rows">{fmtRows(table.row_count)} rows</div>
                </button>
              {/each}
            </div>
          {/each}
          {#if schemaGroups.length === 0 && browseSearch}
            <div class="no-results">검색 결과가 없습니다.</div>
          {/if}
        </div>

        <div class="table-detail">
          {#if detailLoading}
            <div class="detail-loading">컬럼 정보 로딩 중…</div>
          {:else if detailError}
            <div class="banner fail">✗ {detailError}</div>
          {:else if selectedTable}
            <div class="detail-header">
              <div>
                <h2 class="detail-title">{selectedTable.schema_name}.<strong>{selectedTable.table_name}</strong></h2>
                {#if tableDesc(selectedTable)}
                  <p class="detail-desc">{tableDesc(selectedTable)}</p>
                {/if}
              </div>
              <div class="detail-meta">
                <span class="meta-chip">{fmtRows(selectedTable.row_count)} rows</span>
                {#each (selectedTable.tags ?? []) as tag}
                  <span class="meta-chip tag">{tag}</span>
                {/each}
              </div>
            </div>

            <table class="columns-table">
              <thead>
                <tr>
                  <th>#</th><th>컬럼명</th><th>타입</th><th>Null</th><th>키</th><th>설명</th>
                </tr>
              </thead>
              <tbody>
                {#each selectedTable.columns.sort((a, b) => a.ordinal_position - b.ordinal_position) as col}
                  <tr>
                    <td class="col-pos">{col.ordinal_position}</td>
                    <td class="col-name">{col.column_name}</td>
                    <td class="col-type">{col.data_type}</td>
                    <td>{col.is_nullable ? '✓' : ''}</td>
                    <td>
                      {#if col.is_primary_key}<span class="key pk">PK</span>{/if}
                      {#if col.is_foreign_key}<span class="key fk" title={col.references_column ?? ''}>FK</span>{/if}
                    </td>
                    <td class="col-desc">{col.user_description ?? col.source_description ?? ''}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          {:else}
            <div class="empty-detail">
              <p>왼쪽에서 테이블을 선택하세요.</p>
            </div>
          {/if}
        </div>
      </div>
    {/if}

  <!-- ── Search mode ── -->
  {:else}
    <div class="search-area">
      <div class="search-bar">
        <input
          bind:value={query}
          on:keydown={onSearchKeydown}
          placeholder="예: 월별 매출 집계, 고객 등급, 이벤트 로그…"
          disabled={searching}
          autofocus
        />
        <button class="btn-search" on:click={runSearch} disabled={searching || !query.trim()}>
          {searching ? '검색 중…' : '검색'}
        </button>
      </div>

      {#if searching}
        <div class="loading">벡터 유사도 검색 중…</div>
      {:else if searched && searchError}
        <div class="banner fail">✗ {searchError}</div>
      {:else if searched}
        <div class="results-header">
          <span class="results-count">{searchResults.length}개 결과</span>
          <span class="results-hint">관련도 순 · {searchTimeMs}ms</span>
        </div>
        {#if searchResults.length === 0}
          <div class="search-empty">
            <div class="search-empty-icon">🔍</div>
            <p>관련 테이블/컬럼을 찾지 못했습니다.</p>
          </div>
        {:else}
          <div class="results-list">
            {#each searchResults as result}
              <div class="result-card">
                <div class="result-top">
                  <div class="result-title-row">
                    <span
                      class="doc-type-badge"
                      style="background:{DOC_TYPE_COLOR[result.type]}18; color:{DOC_TYPE_COLOR[result.type]}"
                    >
                      {TYPE_LABEL[result.type]}
                    </span>
                    <span class="result-title">
                      {result.table_name}{result.column_name ? '.' + result.column_name : ''}
                    </span>
                  </div>
                  <div class="score-bar-wrap">
                    <div class="score-bar" style="width:{scorePct(result.relevance_score)}%"></div>
                    <span class="score-label">{scorePct(result.relevance_score)}%</span>
                  </div>
                </div>
                {#if result.snippet}
                  <p class="result-snippet">{result.snippet}</p>
                {/if}
                <div class="result-path">
                  {result.schema_name}.{result.table_name}{result.column_name ? '.' + result.column_name : ''}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      {:else}
        <div class="search-empty">
          <div class="search-empty-icon">🔍</div>
          <p>검색어를 입력하면 벡터 유사도 기반으로 관련 테이블·컬럼을 찾아드립니다.</p>
        </div>
      {/if}
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

  .header-right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

  /* Mode tabs */
  .mode-tabs {
    display: flex;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    overflow: hidden;
  }
  .mode-tab {
    padding: 7px 18px;
    background: #fff;
    border: none;
    font-size: 13px;
    font-weight: 500;
    color: #6b7280;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
  }
  .mode-tab + .mode-tab { border-left: 1px solid #e5e7eb; }
  .mode-tab:hover { background: #f9fafb; color: #374151; }
  .mode-tab.active { background: #eff6ff; color: #1d4ed8; }

  .btn-refresh {
    padding: 7px 14px;
    background: #fff;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 13px;
    cursor: pointer;
  }
  .btn-refresh:hover:not(:disabled) { background: #f3f4f6; }
  .btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }

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

  /* Banners */
  .banner {
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }
  .banner.ok { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
  .banner.fail { background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }
  .banner button { background: transparent; border: none; color: inherit; text-decoration: underline; cursor: pointer; font-size: 13px; padding: 0; }

  /* ── Browse ── */
  .browse-toolbar {
    margin-bottom: 12px;
    flex-shrink: 0;
  }
  .browse-search {
    padding: 8px 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 13px;
    outline: none;
    width: 220px;
  }
  .browse-search:focus { border-color: #2563eb; }

  .loading { padding: 48px; text-align: center; color: #9ca3af; font-size: 14px; flex-shrink: 0; }

  .empty-catalog {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: #9ca3af;
    text-align: center;
  }
  .empty-catalog p { margin: 0; font-size: 14px; }
  .empty-catalog .hint { font-size: 13px; color: #d1d5db; }

  .catalog-layout {
    display: flex;
    gap: 16px;
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  .table-list {
    width: 220px;
    min-width: 220px;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    background: #fff;
    padding: 8px;
  }
  .schema-group { margin-bottom: 12px; }
  .schema-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #9ca3af;
    padding: 4px 8px 2px;
  }
  .table-cnt {
    font-size: 10px;
    background: #f3f4f6;
    color: #6b7280;
    padding: 1px 5px;
    border-radius: 8px;
    font-weight: 500;
  }
  .table-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
    width: 100%;
    text-align: left;
    padding: 8px;
    border-radius: 6px;
    border: none;
    background: transparent;
    cursor: pointer;
    font-size: 13px;
  }
  .table-item:hover { background: #f3f4f6; }
  .table-item.active { background: #eff6ff; }
  .table-item-top { display: flex; align-items: center; justify-content: space-between; gap: 4px; }
  .table-name { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .table-type {
    font-size: 10px;
    padding: 1px 5px;
    border-radius: 3px;
    background: #f3f4f6;
    color: #6b7280;
    flex-shrink: 0;
  }
  .table-type.view { background: #fef3c7; color: #92400e; }
  .table-rows { font-size: 11px; color: #9ca3af; }
  .no-results { padding: 16px; color: #9ca3af; font-size: 13px; text-align: center; }

  .table-detail {
    flex: 1;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    background: #fff;
    padding: 20px;
  }
  .detail-loading { padding: 32px; text-align: center; color: #9ca3af; font-size: 14px; }
  .detail-header { margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
  h2.detail-title { margin: 0 0 4px; font-size: 18px; font-weight: 400; }
  h2 strong { font-weight: 700; }
  .detail-desc { margin: 0; color: #6b7280; font-size: 13px; }
  .detail-meta { display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; flex-shrink: 0; }
  .meta-chip { font-size: 12px; padding: 3px 10px; border-radius: 12px; background: #f3f4f6; color: #374151; }
  .meta-chip.tag { background: #eff6ff; color: #1d4ed8; }

  .columns-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .columns-table th {
    text-align: left;
    padding: 8px 12px;
    border-bottom: 2px solid #e5e7eb;
    color: #6b7280;
    font-size: 12px;
    font-weight: 600;
  }
  .columns-table td { padding: 8px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: middle; }
  .col-pos { color: #9ca3af; font-size: 11px; text-align: right; width: 28px; }
  .col-name { font-weight: 500; font-family: 'Cascadia Code', monospace; }
  .col-type { color: #2563eb; font-family: 'Cascadia Code', monospace; font-size: 12px; }
  .col-desc { color: #6b7280; }
  .key { font-size: 10px; font-weight: 700; padding: 1px 5px; border-radius: 3px; margin-right: 2px; }
  .pk { background: #fef3c7; color: #92400e; }
  .fk { background: #e0e7ff; color: #3730a3; }
  .empty-detail { display: flex; align-items: center; justify-content: center; height: 100%; color: #9ca3af; font-size: 14px; }

  /* ── Search ── */
  .search-area { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow-y: auto; max-width: 800px; }

  .search-bar { display: flex; gap: 8px; margin-bottom: 20px; flex-shrink: 0; }
  .search-bar input {
    flex: 1;
    padding: 10px 14px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 14px;
    outline: none;
  }
  .search-bar input:focus { border-color: #2563eb; }
  .search-bar input:disabled { background: #f9fafb; }

  .btn-search {
    padding: 10px 24px;
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }
  .btn-search:hover:not(:disabled) { background: #1d4ed8; }
  .btn-search:disabled { opacity: 0.5; cursor: not-allowed; }

  .results-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-shrink: 0; }
  .results-count { font-size: 13px; font-weight: 600; color: #374151; }
  .results-hint { font-size: 12px; color: #9ca3af; }

  .results-list { display: flex; flex-direction: column; gap: 10px; }

  .result-card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; background: #fff; }
  .result-top { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 8px; }
  .result-title-row { display: flex; align-items: center; gap: 8px; overflow: hidden; }
  .doc-type-badge { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; flex-shrink: 0; }
  .result-title { font-size: 14px; font-weight: 600; font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .score-bar-wrap { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
  .score-bar { height: 4px; background: #2563eb; border-radius: 2px; min-width: 4px; max-width: 80px; }
  .score-label { font-size: 12px; color: #6b7280; min-width: 34px; text-align: right; }

  .result-snippet {
    margin: 0 0 8px;
    font-size: 13px;
    color: #4b5563;
    font-family: 'Cascadia Code', monospace;
    background: #f9fafb;
    padding: 6px 10px;
    border-radius: 6px;
    white-space: pre-wrap;
    word-break: break-all;
  }
  .result-path { font-size: 12px; color: #9ca3af; font-family: monospace; }

  .search-empty { display: flex; flex-direction: column; align-items: center; padding: 64px 32px; color: #9ca3af; text-align: center; gap: 12px; }
  .search-empty-icon { font-size: 36px; }
  .search-empty p { margin: 0; font-size: 14px; max-width: 380px; }
</style>
