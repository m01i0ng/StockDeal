<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { showToast } from "vant";
import { createFundConversion, createFundTransaction, getFundAccountDetail } from "../api";
import type { FundAccountDetailResponse } from "../api";

const route = useRoute();
const router = useRouter();
const activeTab = ref(0);
const account = ref<FundAccountDetailResponse | null>(null);
const isLoading = ref(false);

const accountId = computed(() => Number(route.query.account_id));
const accountName = computed(() => account.value?.name ?? "未选择账户");
const canSubmit = computed(() => !isLoading.value && !!accountId.value);
const todayLabel = computed(() => {
  const now = new Date();
  return now.toISOString().slice(0, 10);
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

const tradeForm = ref({
  fund_code: "",
  amount: "",
  trade_date: todayLabel.value,
  is_after_cutoff: false,
  remark: "",
});

const conversionForm = ref({
  from_fund_code: "",
  to_fund_code: "",
  from_amount: "",
  to_amount: "",
  trade_date: todayLabel.value,
  is_after_cutoff: false,
  remark: "",
});

const resetTradeForm = () => {
  tradeForm.value = {
    fund_code: "",
    amount: "",
    trade_date: todayLabel.value,
    is_after_cutoff: false,
    remark: "",
  };
};

const resetConversionForm = () => {
  conversionForm.value = {
    from_fund_code: "",
    to_fund_code: "",
    from_amount: "",
    to_amount: "",
    trade_date: todayLabel.value,
    is_after_cutoff: false,
    remark: "",
  };
};

const isSubmitting = ref(false);

const submitTrade = async (tradeType: "buy" | "sell") => {
  if (!accountId.value) {
    return;
  }
  if (!tradeForm.value.fund_code || !tradeForm.value.amount || !tradeForm.value.trade_date) {
    return;
  }
  isSubmitting.value = true;
  try {
    await createFundTransaction({
      account_id: accountId.value,
      fund_code: tradeForm.value.fund_code.trim(),
      trade_type: tradeType,
      amount: Number(tradeForm.value.amount),
      trade_date: tradeForm.value.trade_date,
      is_after_cutoff: tradeForm.value.is_after_cutoff,
      remark: tradeForm.value.remark.trim() || null,
    });
    resetTradeForm();
    showToast("保存成功");
    await router.push(`/accounts/${accountId.value}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : "保存失败";
    showToast(message);
  } finally {
    isSubmitting.value = false;
  }
};

const submitConversion = async () => {
  if (!accountId.value) {
    return;
  }
  const form = conversionForm.value;
  if (!form.from_fund_code || !form.to_fund_code || !form.from_amount || !form.to_amount) {
    return;
  }
  if (!form.trade_date) {
    return;
  }
  isSubmitting.value = true;
  try {
    await createFundConversion({
      account_id: accountId.value,
      from_fund_code: form.from_fund_code.trim(),
      to_fund_code: form.to_fund_code.trim(),
      from_amount: Number(form.from_amount),
      to_amount: Number(form.to_amount),
      trade_date: form.trade_date,
      is_after_cutoff: form.is_after_cutoff,
      remark: form.remark.trim() || null,
    });
    resetConversionForm();
    showToast("保存成功");
    await router.push(`/accounts/${accountId.value}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : "保存失败";
    showToast(message);
  } finally {
    isSubmitting.value = false;
  }
};

const tabs = [
  {
    key: "buy",
    title: "买入",
    hint: "记录资金流入，完善买入时间与金额。",
  },
  {
    key: "sell",
    title: "卖出",
    hint: "填写卖出份额与价格，便于收益统计。",
  },
  {
    key: "transfer",
    title: "转换",
    hint: "记录基金间转换，保持账户净值追踪。",
  },
];
</script>

<template>
  <section class="page-section">
    <header class="page-header">
      <div>
        <p class="page-kicker">新增流水</p>
        <h1 class="page-title">添加流水</h1>
      </div>
      <van-tag type="primary" round>模板</van-tag>
    </header>

    <van-cell-group inset>
      <van-cell title="账户" :value="accountName" />
      <van-cell title="资金日期" :value="todayLabel" />
    </van-cell-group>

    <van-tabs v-model:active="activeTab" class="transaction-tabs" swipeable>
      <van-tab v-for="tab in tabs" :key="tab.key" :title="tab.title">
        <div class="transaction-panel">
          <p class="transaction-hint">{{ tab.hint }}</p>
          <template v-if="tab.key !== 'transfer'">
            <van-field v-model="tradeForm.fund_code" label="基金代码" placeholder="输入基金代码" />
            <van-field
              v-model="tradeForm.amount"
              label="金额"
              placeholder="输入金额"
              type="number"
            />
            <van-field
              v-model="tradeForm.trade_date"
              label="交易日期"
              placeholder="选择交易日期"
              type="date"
            />
            <van-field label="15点后交易">
              <template #input>
                <van-switch v-model="tradeForm.is_after_cutoff" size="20" />
              </template>
            </van-field>
            <van-field v-model="tradeForm.remark" label="备注" placeholder="填写备注" />
            <van-button
              type="primary"
              block
              round
              :loading="isSubmitting"
              :disabled="!canSubmit"
              @click="submitTrade(tab.key === 'buy' ? 'buy' : 'sell')"
            >
              保存{{ tab.title }}流水
            </van-button>
          </template>
          <template v-else>
            <van-field
              v-model="conversionForm.from_fund_code"
              label="转出基金"
              placeholder="输入转出基金代码"
            />
            <van-field
              v-model="conversionForm.to_fund_code"
              label="转入基金"
              placeholder="输入转入基金代码"
            />
            <van-field
              v-model="conversionForm.from_amount"
              label="转出金额"
              placeholder="输入转出金额"
              type="number"
            />
            <van-field
              v-model="conversionForm.to_amount"
              label="转入金额"
              placeholder="输入转入金额"
              type="number"
            />
            <van-field
              v-model="conversionForm.trade_date"
              label="交易日期"
              placeholder="选择交易日期"
              type="date"
            />
            <van-field label="15点后交易">
              <template #input>
                <van-switch v-model="conversionForm.is_after_cutoff" size="20" />
              </template>
            </van-field>
            <van-field v-model="conversionForm.remark" label="备注" placeholder="填写备注" />
            <van-button
              type="primary"
              block
              round
              :loading="isSubmitting"
              :disabled="!canSubmit"
              @click="submitConversion"
            >
              保存转换流水
            </van-button>
          </template>
        </div>
      </van-tab>
    </van-tabs>
  </section>
</template>
