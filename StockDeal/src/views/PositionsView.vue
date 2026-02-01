<template>
  <section class="page-section">
    <header class="page-header">
      <div>
        <p class="page-kicker">投资组合</p>
        <h1 class="page-title">持仓</h1>
      </div>
      <van-button type="primary" size="small" round>调仓</van-button>
    </header>

    <van-cell-group inset>
      <van-cell title="核心持仓" value="6 只" />
      <van-cell title="今日收益" value="+0.62%" />
      <van-cell title="最大回撤" value="-3.1%" />
    </van-cell-group>

    <div class="page-block">
      <van-empty description="暂无更多持仓数据" />
    </div>
  </section>
</template>
