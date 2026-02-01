<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { listFundAccounts } from "../api";
import type { FundAccountResponse } from "../api";

const accounts = ref<FundAccountResponse[]>([]);
const isLoading = ref(false);

const accountCount = computed(() => `${accounts.value.length} 个`);

const fetchAccounts = async () => {
  isLoading.value = true;
  try {
    accounts.value = await listFundAccounts();
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchAccounts);
</script>

<template>
  <section class="page-section">
    <header class="page-header">
      <div>
        <p class="page-kicker">投资组合</p>
        <h1 class="page-title">持仓管理</h1>
      </div>
    </header>

    <van-cell-group inset>
      <van-cell title="账户总数" :value="accountCount" />
      <van-cell title="组合总值" value="请在账户内查看" />
      <van-cell title="今日收益" value="以账户收益为准" />
    </van-cell-group>

    <div class="page-block">
      <van-cell-group inset>
        <van-cell
          v-for="account in accounts"
          :key="account.id"
          :title="account.name"
          :label="account.remark || '暂无备注'"
          :value="`费率 ${account.default_buy_fee_percent}%`"
          is-link
          :to="`/accounts/${account.id}`"
        />
      </van-cell-group>

      <van-button
        class="account-create-button"
        type="primary"
        round
        block
        to="/accounts/new"
        :loading="isLoading"
      >
        新建账户
      </van-button>
    </div>
  </section>
</template>
