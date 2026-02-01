<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Dialog } from "vant";
import { deleteFundHolding, getFundHoldingDetail, updateFundHolding } from "../api";
import type { FundHoldingPositionResponse } from "../api";

const route = useRoute();
const router = useRouter();

const holding = ref<FundHoldingPositionResponse | null>(null);
const isLoading = ref(false);
const isSubmitting = ref(false);
const isDeleting = ref(false);

const holdingId = computed(() => Number(route.params.id));

const form = ref({
  total_amount: "",
  total_shares: "",
});

const syncForm = (detail: FundHoldingPositionResponse) => {
  form.value = {
    total_amount: detail.total_amount.toString(),
    total_shares: detail.total_shares.toString(),
  };
};

const handleDelete = async () => {
  if (!holdingId.value || isDeleting.value) {
    return;
  }
  try {
    await Dialog.confirm({
      title: "删除持仓",
      message: "确认删除该持仓吗？该操作无法撤销。",
      confirmButtonColor: "#ef4444",
    });
  } catch (error) {
    if (error === "cancel") {
      return;
    }
    throw error;
  }

  isDeleting.value = true;
  try {
    await deleteFundHolding(holdingId.value);
    await router.replace(`/accounts/${holding.value?.account_id ?? ""}`);
  } finally {
    isDeleting.value = false;
  }
};

const fetchDetail = async () => {
  if (!holdingId.value) {
    return;
  }
  isLoading.value = true;
  try {
    const detail = await getFundHoldingDetail(holdingId.value);
    holding.value = detail;
    syncForm(detail);
  } finally {
    isLoading.value = false;
  }
};

const handleSubmit = async () => {
  if (!holdingId.value) {
    return;
  }
  if (!form.value.total_amount || !form.value.total_shares) {
    return;
  }
  isSubmitting.value = true;
  try {
    const detail = await updateFundHolding(holdingId.value, {
      total_amount: Number(form.value.total_amount),
      total_shares: Number(form.value.total_shares),
    });
    holding.value = detail;
    syncForm(detail);
    await router.replace(`/holdings/${holdingId.value}`);
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(fetchDetail);
</script>

<template>
  <section class="page-section">
    <header class="page-header">
      <div>
        <p class="page-kicker">持仓详情</p>
        <h1 class="page-title">{{ holding?.fund_code || "持仓详情" }}</h1>
      </div>
      <van-tag type="primary" round>详情</van-tag>
    </header>

    <van-cell-group inset>
      <van-cell title="基金代码" :value="holding?.fund_code || '--'" />
      <van-cell title="预估净值" :value="holding?.estimated_nav ?? '--'" />
      <van-cell title="预估市值" :value="holding?.estimated_value ?? '--'" />
      <van-cell title="预估收益" :value="holding?.estimated_profit ?? '--'" />
    </van-cell-group>

    <van-cell-group inset class="form-card">
      <van-field
        v-model="form.total_amount"
        label="持仓金额"
        placeholder="输入持仓金额"
        type="number"
      />
      <van-field
        v-model="form.total_shares"
        label="持仓份额"
        placeholder="输入持仓份额"
        type="number"
      />
    </van-cell-group>

    <div class="form-actions">
      <van-button
        type="primary"
        block
        round
        :loading="isSubmitting"
        :disabled="isLoading || isDeleting"
        @click="handleSubmit"
      >
        保存修改
      </van-button>
    </div>

    <van-tabbar class="detail-tabbar" fixed safe-area-inset-bottom>
      <van-tabbar-item icon="delete-o" @click="handleDelete">删除持仓</van-tabbar-item>
    </van-tabbar>
  </section>
</template>
