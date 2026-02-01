<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { showToast } from "vant";
import { createFundHolding } from "../api";

const route = useRoute();
const router = useRouter();

const accountId = computed(() => Number(route.query.account_id));
const isSubmitting = ref(false);

const form = ref({
  fund_code: "",
  total_amount: "",
  profit_amount: "",
  remark: "",
});

const handleSubmit = async () => {
  if (!accountId.value) {
    showToast("缺少账户信息");
    return;
  }
  if (!form.value.fund_code || !form.value.total_amount || !form.value.profit_amount) {
    showToast("请填写完整信息");
    return;
  }
  isSubmitting.value = true;
  try {
    await createFundHolding({
      account_id: accountId.value,
      fund_code: form.value.fund_code.trim(),
      total_amount: Number(form.value.total_amount),
      profit_amount: Number(form.value.profit_amount),
      remark: form.value.remark.trim() || null,
    });
    showToast("添加成功");
    form.value = {
      fund_code: "",
      total_amount: "",
      profit_amount: "",
      remark: "",
    };
    await router.push(`/accounts/${accountId.value}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : "添加失败";
    showToast(message);
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
  <section class="page-section">
    <header class="page-header">
      <div>
        <p class="page-kicker">账户持仓</p>
        <h1 class="page-title">添加持仓</h1>
      </div>
    </header>

    <van-cell-group inset class="form-card">
      <van-field v-model="form.fund_code" label="基金代码" placeholder="输入基金代码" />
      <van-field
        v-model="form.total_amount"
        label="总额"
        placeholder="输入总额"
        type="number"
      />
      <van-field
        v-model="form.profit_amount"
        label="收益额"
        placeholder="输入收益额"
        type="number"
      />
      <van-field v-model="form.remark" label="备注" placeholder="填写备注" />
    </van-cell-group>

    <div class="form-actions">
      <van-button type="primary" block round :loading="isSubmitting" @click="handleSubmit">
        保存持仓
      </van-button>
    </div>
  </section>
</template>
