<script lang="ts">
  export let sql: string;

  let copied = false;

  async function copy() {
    await navigator.clipboard.writeText(sql);
    copied = true;
    setTimeout(() => (copied = false), 1500);
  }
</script>

<div class="sql-block">
  <div class="sql-header">
    <span class="sql-label">SQL</span>
    <button class="copy-btn" on:click={copy}>{copied ? 'Copied ✓' : 'Copy'}</button>
  </div>
  <pre class="sql-code">{sql}</pre>
</div>

<style>
  .sql-block {
    background: #0b1120;
    border-radius: 8px;
    overflow: hidden;
    margin: 8px 0;
    border: 1px solid #1e2d45;
  }

  .sql-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 12px;
    background: #111e30;
    border-bottom: 1px solid #1e2d45;
  }

  .sql-label {
    font-size: 11px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .copy-btn {
    font-size: 12px;
    color: #93c5fd;
    background: none;
    border: none;
    cursor: pointer;
    padding: 2px 8px;
    border-radius: 4px;
  }
  .copy-btn:hover { background: #1e2d45; }

  .sql-code {
    margin: 0;
    padding: 12px;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 12.5px;
    line-height: 1.6;
    color: #93c5fd;
    white-space: pre-wrap;
    word-break: break-word;
  }
</style>
