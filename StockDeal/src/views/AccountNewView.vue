<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { createFundAccount } from "../api";

const router = useRouter();
const isSubmitting = ref(false);

const form = reactive({
  name: "",
  remark: "",
  default_buy_fee_percent: 0,
});

const handleSubmit = async () => {
  if (!form.name.trim()) {
    return;
  }
  isSubmitting.value = true;
  try {
    const created = await createFundAccount({
      name: form.name.trim(),
      remark: form.remark.trim() || null,
      default_buy_fee_percent: form.default_buy_fee_percent,
    });
    router.push(`/accounts/${created.id}`);
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
  <section class="page-section">
    <header class="page-header">
      <div>
        <p class="page-kicker">账户管理</p>
        <h1 class="page-title">新建账户</h1>
      </div>
    </header>

    <van-cell-group inset class="form-card">
      <van-field v-model="form.name" label="账户名称" placeholder="例如：主账户" />
      <van-field v-model="form.remark" label="备注" placeholder="可选" />
      <van-field
        v-model.number="form.default_buy_fee_percent"
        label="默认买入费率"
        placeholder="例如：0.15"
        type="number"
      />
    </van-cell-group>

    <div class="form-actions">
      <van-button type="primary" block round :loading="isSubmitting" @click="handleSubmit">
        保存账户
      </van-button>
    </div>
  </section>
</template>
