<template>
  <section class="page-section">
    <header class="page-header">
      <div>
        <p class="page-kicker">关注列表</p>
        <h1 class="page-title">自选</h1>
      </div>
      <van-button type="default" size="small" round>新增</van-button>
    </header>

    <van-cell-group inset>
      <van-cell title="观察基金" value="12 只" />
      <van-cell title="今日涨幅" value="+0.85%" />
      <van-cell title="预警" value="2 条" />
    </van-cell-group>

    <div class="page-block">
      <van-empty description="暂无自选数据" />
    </div>
  </section>
</template>
