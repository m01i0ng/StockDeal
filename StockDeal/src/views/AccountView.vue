<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { getFundAccountDetail } from "../api";
import type { FundAccountDetailResponse } from "../api";

const route = useRoute();

const account = ref<FundAccountDetailResponse | null>(null);
const isLoading = ref(false);

const accountId = computed(() => Number(route.params.id));
const profitClass = computed(() => {
  const profit = account.value?.total_profit ?? 0;
  return profit < 0 ? "account-profit is-negative" : "account-profit";
});

const fetchAccount = async () => {
  if (!accountId.value) {
    account.value = null;
    return;
  }
  isLoading.value = true;
  try {
    account.value = await getFundAccountDetail(accountId.value);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchAccount);
watch(accountId, fetchAccount);
</script>

<template>
  <section class="page-section">
    <header class="page-header">
      <div>
        <p class="page-kicker">账户概览</p>
        <h1 class="page-title">{{ account?.name || "账户详情" }}</h1>
      </div>
      <van-tag type="primary" round>运行中</van-tag>
    </header>

    <div class="account-hero">
      <div>
        <p class="account-label">组合市值</p>
        <h2 class="account-value">{{ account?.total_value ?? "--" }}</h2>
      </div>
      <div class="account-meta">
        <div>
          <p class="account-label">累计收益</p>
          <p :class="profitClass">{{ account?.total_profit ?? "--" }}</p>
        </div>
        <div>
          <p class="account-label">今日涨幅</p>
          <p class="account-profit">{{ account?.total_profit_percent ?? "--" }}</p>
        </div>
      </div>
    </div>

    <van-cell-group inset>
      <van-cell title="账户备注" :value="account?.remark || '暂无备注'" />
      <van-cell title="持仓数量" :value="account?.holdings.length ?? '--'" />
      <van-cell title="默认买入费率" :value="account ? `${account.default_buy_fee_percent}%` : '--'" />
    </van-cell-group>

    <div class="page-block">
      <van-cell-group inset>
        <van-cell
          v-for="position in account?.holdings || []"
          :key="position.holding_id"
          :title="position.fund_code"
          :label="`持仓 ${position.total_shares}`"
          :value="position.estimated_value ?? position.total_amount"
          is-link
          :to="`/holdings/${position.holding_id}`"
        />
      </van-cell-group>
      <van-empty v-if="!isLoading && (account?.holdings.length ?? 0) === 0" description="暂无持仓" />
    </div>
  </section>
</template>
