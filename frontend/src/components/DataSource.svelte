<script lang="ts">
  import { onMount } from 'svelte';
  import { dataSourceApi, ApiError } from '../lib/api';
  import type { DataSource, DataSourceType } from '../lib/types';
  import { dataSources, selectedDataSource } from '../lib/stores';
  import { MOCK_DATA_SOURCE } from '../lib/mock';
  import { language, t } from '../lib/i18n';

  // ── State ─────────────────────────────────────────────────────────────────
  let sources: DataSource[] = $dataSources;
  let loading = false;
  let error = '';

  // Form state
  let showForm = false;
  let formType: DataSourceType = 'postgresql';
  let formName = '';
  let formDesc = '';
  // PostgreSQL / Redshift config
  let pgHost = '';
  let pgPort = 5432;
  let pgDatabase = '';
  let pgUsername = '';
  let pgPassword = '';
  // Trino config
  let trinoUrl = '';
  let trinoCatalog = '';
  let trinoUsername = '';
  let trinoPassword = '';

  let formLoading = false;
  let formError = '';

  // Pre-save connection test
  let formTestLoading = false;
  let formTestResult: { ok: boolean; text: string } | null = null;

  // Per-row test/sync state
  let testingId: string | null = null;
  let syncingId: string | null = null;
  let rowMessages: Record<string, { ok: boolean; text: string }> = {};

  $: dateLocale = $language === 'ko' ? 'ko-KR' : 'en-US';
  $: statusLabel = {
    connected: $t('ds.status.connected'),
    disconnected: $t('ds.status.disconnected'),
    error: $t('ds.status.error'),
  } as Record<string, string>;

  onMount(load);

  async function load() {
    loading = true;
    error = '';
    try {
      const apiSources = await dataSourceApi.list();
      const existingMocks = $dataSources.filter(
        s => s.type === 'mockup' && !apiSources.find(a => a.id === s.id),
      );
      sources = [...apiSources, ...existingMocks];
      dataSources.set(sources);
      selectedDataSource.update(cur => {
        if (!cur) return sources[0] ?? null;
        return sources.find(s => s.id === cur.id) ?? (sources[0] ?? null);
      });
    } catch (e) {
      error = e instanceof ApiError ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  function buildConfig(): Record<string, unknown> {
    if (formType === 'mockup') return {};
    if (formType === 'trino') {
      return {
        coordinator_url: trinoUrl,
        catalog: trinoCatalog,
        username: trinoUsername,
        ...(trinoPassword ? { password: trinoPassword } : {}),
      };
    }
    return {
      host: pgHost,
      port: pgPort,
      database: pgDatabase,
      username: pgUsername,
      password: pgPassword,
    };
  }

  function resetConfigFields() {
    pgHost = ''; pgPort = 5432; pgDatabase = ''; pgUsername = ''; pgPassword = '';
    trinoUrl = ''; trinoCatalog = ''; trinoUsername = ''; trinoPassword = '';
    formTestResult = null;
    formError = '';
  }

  function resetForm() {
    formName = ''; formDesc = ''; formType = 'postgresql';
    resetConfigFields();
  }

  async function testFormConn() {
    formTestLoading = true;
    formTestResult = null;
    try {
      const res = await dataSourceApi.testConnectionDirect({
        type: formType,
        config: buildConfig(),
      });
      formTestResult = { ok: res.success, text: res.message };
    } catch (e) {
      formTestResult = { ok: false, text: e instanceof ApiError ? e.message : String(e) };
    } finally {
      formTestLoading = false;
    }
  }

  async function create() {
    formError = '';
    if (!formName.trim()) { formError = $t('ds.error.name'); return; }
    formLoading = true;
    try {
      if (formType === 'mockup') {
        const newMock: DataSource = {
          ...MOCK_DATA_SOURCE,
          id: `__mockup__${crypto.randomUUID()}`,
          name: formName.trim(),
          description: formDesc.trim() || MOCK_DATA_SOURCE.description,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        sources = [...sources, newMock];
        dataSources.set(sources);
        selectedDataSource.update(cur => cur ?? newMock);
      } else {
        await dataSourceApi.create({
          name: formName.trim(),
          type: formType,
          description: formDesc.trim() || undefined,
          config: buildConfig(),
        });
        await load();
      }
      resetForm();
      showForm = false;
    } catch (e) {
      formError = e instanceof ApiError ? e.message : String(e);
    } finally {
      formLoading = false;
    }
  }

  async function remove(id: string, name: string, isMock: boolean) {
    if (!confirm($t('ds.confirm.delete', { name }))) return;
    try {
      if (isMock) {
        sources = sources.filter(s => s.id !== id);
        dataSources.set(sources);
        selectedDataSource.update(cur => (cur?.id === id ? sources[0] ?? null : cur));
      } else {
        await dataSourceApi.delete(id);
        await load();
      }
    } catch (e) {
      error = e instanceof ApiError ? e.message : String(e);
    }
  }

  async function testConn(id: string) {
    testingId = id;
    rowMessages = { ...rowMessages, [id]: undefined };
    try {
      const res = await dataSourceApi.testConnection(id);
      rowMessages = { ...rowMessages, [id]: { ok: res.success, text: res.message } };
      await load();
    } catch (e) {
      rowMessages = { ...rowMessages, [id]: { ok: false, text: String(e) } };
    } finally {
      testingId = null;
    }
  }

  async function syncSource(id: string) {
    syncingId = id;
    rowMessages = { ...rowMessages, [id]: undefined };
    try {
      const res = await dataSourceApi.sync(id);
      rowMessages = { ...rowMessages, [id]: { ok: true, text: res.message } };
      await load();
    } catch (e) {
      rowMessages = { ...rowMessages, [id]: { ok: false, text: String(e) } };
    } finally {
      syncingId = null;
    }
  }

  const STATUS_COLOR: Record<string, string> = {
    connected: '#16a34a',
    disconnected: '#6b7280',
    error: '#dc2626',
  };

  function fmtDate(iso: string | null) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString(dateLocale, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }
</script>

<div class="page">
  <div class="page-header">
    <div>
      <h1>{$t('ds.title')}</h1>
      <p class="subtitle">{$t('ds.subtitle')}</p>
    </div>
    <button class="btn-primary" on:click={() => { showForm = !showForm; if (!showForm) resetForm(); }}>
      {showForm ? $t('common.cancel') : $t('ds.btn.new')}
    </button>
  </div>

  <!-- ── Create form ─────────────────────────────────── -->
  {#if showForm}
    <div class="card form-card">
      <h3>{$t('ds.form.title')}</h3>

      <div class="field-row">
        <div class="field">
          <label>{$t('ds.field.name')}</label>
          <input bind:value={formName} placeholder="my-postgres" />
        </div>
        <div class="field">
          <label>{$t('ds.field.type')}</label>
          <select bind:value={formType} on:change={resetConfigFields}>
            <option value="postgresql">PostgreSQL</option>
            <option value="redshift">Redshift</option>
            <option value="trino">Trino</option>
            <option value="mockup">{$t('ds.mockup.option')}</option>
          </select>
        </div>
        <div class="field flex2">
          <label>{$t('ds.field.desc')}</label>
          <input bind:value={formDesc} placeholder={$t('common.optional')} />
        </div>
      </div>

      {#if formType === 'mockup'}
        <div class="mock-notice">
          {$t('ds.mockup.notice')}
        </div>
      {:else if formType === 'trino'}
        <div class="field-row">
          <div class="field flex2">
            <label>Coordinator URL *</label>
            <input bind:value={trinoUrl} placeholder="http://trino-host:8080" />
          </div>
          <div class="field">
            <label>Catalog *</label>
            <input bind:value={trinoCatalog} placeholder="hive" />
          </div>
          <div class="field">
            <label>Username *</label>
            <input bind:value={trinoUsername} placeholder="trino" />
          </div>
          <div class="field">
            <label>Password</label>
            <input type="password" bind:value={trinoPassword} />
          </div>
        </div>
      {:else}
        <!-- postgresql / redshift -->
        <div class="field-row">
          <div class="field flex2">
            <label>Host *</label>
            <input bind:value={pgHost} placeholder="localhost" />
          </div>
          <div class="field small">
            <label>Port</label>
            <input type="number" bind:value={pgPort} />
          </div>
          <div class="field">
            <label>Database *</label>
            <input bind:value={pgDatabase} placeholder="mydb" />
          </div>
          <div class="field">
            <label>Username *</label>
            <input bind:value={pgUsername} placeholder="postgres" />
          </div>
          <div class="field">
            <label>Password *</label>
            <input type="password" bind:value={pgPassword} />
          </div>
        </div>
      {/if}

      {#if formTestResult}
        <div class="row-msg" class:ok={formTestResult.ok} class:fail={!formTestResult.ok}>
          {formTestResult.ok ? '✓ ' : '✗ '}{formTestResult.text}
        </div>
      {/if}

      {#if formError}
        <p class="form-error">{formError}</p>
      {/if}

      <div class="form-actions">
        <button class="btn-secondary" on:click={() => { showForm = false; resetForm(); }}>{$t('common.cancel')}</button>
        {#if formType !== 'mockup'}
          <button class="btn-outline-blue" on:click={testFormConn} disabled={formTestLoading || formLoading}>
            {formTestLoading ? $t('ds.btn.testing') : $t('ds.btn.test')}
          </button>
        {/if}
        <button class="btn-primary" on:click={create} disabled={formLoading || formTestLoading}>
          {formLoading ? $t('common.saving') : $t('common.save')}
        </button>
      </div>
    </div>
  {/if}

  <!-- ── Error / Loading ─────────────────────────────── -->
  {#if error}
    <div class="banner error">{error} <button on:click={load}>{$t('common.retry')}</button></div>
  {/if}

  <!-- ── Source list ─────────────────────────────────── -->
  {#if loading}
    <div class="loading">{$t('ds.loading')}</div>
  {:else if sources.length === 0}
    <div class="empty">
      <p>{$t('ds.empty.text')}</p>
      <button class="btn-primary" on:click={() => showForm = true}>{$t('ds.empty.cta')}</button>
    </div>
  {:else}
    <div class="source-grid">
      {#each sources as src (src.id)}
        <div class="source-card">
          <div class="card-top">
            <div class="card-meta">
              <span class="src-name">{src.name}</span>
              <span class="src-type" class:mock-type={src.type === 'mockup'}>{src.type}</span>
              {#if src.type === 'mockup'}
                <span class="mock-badge">MOCK</span>
              {/if}
            </div>
            <span class="status-badge" style="background:{STATUS_COLOR[src.status]}20; color:{STATUS_COLOR[src.status]}">
              {statusLabel[src.status] ?? src.status}
            </span>
          </div>

          {#if src.description}
            <p class="src-desc">{src.description}</p>
          {/if}

          <div class="card-info">
            <span>{$t('ds.card.lastSynced')} {fmtDate(src.last_synced)}</span>
          </div>

          {#if rowMessages[src.id]}
            <div class="row-msg" class:ok={rowMessages[src.id].ok} class:fail={!rowMessages[src.id].ok}>
              {rowMessages[src.id].text}
            </div>
          {/if}

          <div class="card-actions">
            {#if src.type === 'mockup'}
              <span class="mock-info">{$t('ds.card.mockInfo')}</span>
            {:else}
              <button
                class="btn-outline"
                on:click={() => testConn(src.id)}
                disabled={testingId === src.id || syncingId === src.id}
              >
                {testingId === src.id ? $t('ds.card.testing') : $t('ds.btn.test')}
              </button>
              <button
                class="btn-outline"
                on:click={() => syncSource(src.id)}
                disabled={testingId === src.id || syncingId === src.id}
              >
                {syncingId === src.id ? $t('ds.card.syncing') : $t('ds.card.syncCatalog')}
              </button>
            {/if}
            <button class="btn-danger" on:click={() => remove(src.id, src.name, src.type === 'mockup')}>{$t('ds.card.delete')}</button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

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

  /* Form */
  .form-card { margin-bottom: 24px; }
  .form-card h3 { margin: 0 0 16px; font-size: 16px; }
  .field-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
  .field { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 140px; }
  .field.flex2 { flex: 2; }
  .field.small { max-width: 100px; }
  label { font-size: 12px; font-weight: 500; color: #374151; }
  input, select {
    padding: 7px 10px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 13px;
    outline: none;
    background: #fff;
  }
  input:focus, select:focus { border-color: #2563eb; }
  .form-error { margin: 4px 0; font-size: 13px; color: #dc2626; }
  .form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }

  /* Buttons */
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
  .btn-secondary {
    padding: 8px 16px;
    background: #fff;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
  }
  .btn-secondary:hover { background: #f9fafb; }
  .btn-outline-blue {
    padding: 8px 16px;
    background: #fff;
    color: #2563eb;
    border: 1px solid #93c5fd;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
  }
  .btn-outline-blue:hover:not(:disabled) { background: #eff6ff; }
  .btn-outline-blue:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-outline {
    padding: 6px 12px;
    background: transparent;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
  }
  .btn-outline:hover:not(:disabled) { background: #f3f4f6; }
  .btn-outline:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-danger {
    padding: 6px 12px;
    background: transparent;
    color: #dc2626;
    border: 1px solid #fca5a5;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
  }
  .btn-danger:hover { background: #fef2f2; }

  /* Banners */
  .banner {
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .banner.error { background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }
  .banner button { background: transparent; border: none; color: inherit; text-decoration: underline; cursor: pointer; font-size: 13px; }

  /* States */
  .loading, .empty { padding: 48px; text-align: center; color: #9ca3af; font-size: 14px; }
  .empty p { margin: 0 0 16px; }

  /* Cards */
  .source-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
  .source-card {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 16px;
    background: #fff;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .card-top { display: flex; justify-content: space-between; align-items: center; }
  .card-meta { display: flex; align-items: center; gap: 8px; }
  .src-name { font-weight: 600; font-size: 15px; }
  .src-type {
    font-size: 11px;
    background: #f3f4f6;
    color: #6b7280;
    padding: 2px 7px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .src-type.mock-type { background: #fef3c7; color: #92400e; }

  .mock-badge {
    font-size: 10px;
    font-weight: 700;
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fcd34d;
    padding: 1px 6px;
    border-radius: 3px;
    letter-spacing: 0.06em;
  }

  .mock-notice {
    padding: 10px 14px;
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 8px;
    font-size: 13px;
    color: #92400e;
    margin-bottom: 4px;
  }

  .mock-info {
    font-size: 12px;
    color: #9ca3af;
    font-style: italic;
    align-self: center;
  }
  .status-badge {
    font-size: 12px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 12px;
  }
  .src-desc { margin: 0; font-size: 13px; color: #6b7280; }
  .card-info { font-size: 12px; color: #9ca3af; }
  .card-actions { display: flex; gap: 6px; flex-wrap: wrap; }

  .row-msg {
    font-size: 12px;
    padding: 6px 10px;
    border-radius: 6px;
  }
  .row-msg.ok { background: #f0fdf4; color: #16a34a; }
  .row-msg.fail { background: #fef2f2; color: #dc2626; }

  /* Card */
  .card {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 20px;
    background: #fff;
  }
</style>
