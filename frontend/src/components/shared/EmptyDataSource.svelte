<script lang="ts">
  import { activeMenu } from '../../lib/stores';

  // 'none'   — 등록된 데이터 소스가 아예 없음
  // 'select' — 소스는 있지만 선택하지 않은 상태
  export let reason: 'none' | 'select' = 'none';
</script>

<div class="empty-wrap">
  <div class="icon">{reason === 'none' ? '🗄️' : '📂'}</div>

  {#if reason === 'none'}
    <p class="title">등록된 데이터 소스가 없습니다</p>
    <p class="desc">이 기능을 사용하려면 먼저 데이터베이스 연결을 등록해야 합니다.</p>
    <button class="cta" on:click={() => activeMenu.set('data-source')}>
      데이터 소스 등록하기 →
    </button>
  {:else}
    <p class="title">데이터 소스를 선택하세요</p>
    <p class="desc">상단 셀렉터에서 작업할 데이터 소스를 선택해 주세요.</p>
  {/if}
</div>

<style>
  .empty-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 320px;
    gap: 12px;
    padding: 40px;
    text-align: center;
    color: #6b7280;
  }

  .icon { font-size: 48px; line-height: 1; }

  .title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #374151;
  }

  .desc {
    margin: 0;
    font-size: 14px;
    max-width: 360px;
    line-height: 1.6;
  }

  .cta {
    margin-top: 8px;
    padding: 10px 20px;
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s;
  }
  .cta:hover { background: #1d4ed8; }
</style>
