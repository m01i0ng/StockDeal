<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const props = defineProps<{
  isAccountPage: boolean;
  actionLink: string | { path: string; query?: Record<string, string> };
  holdingLink: string | { path: string; query?: Record<string, string> };
}>();

const route = useRoute();
const activeTab = computed(() => {
  if (route.path.startsWith("/holdings")) {
    return 0;
  }
  if (route.path.startsWith("/transactions")) {
    return 1;
  }
  return -1;
});
</script>

<template>
  <div
    class="app-action-bar"
    :class="{ 'is-double': props.isAccountPage, 'is-tabbar': props.isAccountPage }"
  >
    <template v-if="props.isAccountPage">
      <van-tabbar
        :model-value="activeTab"
        :fixed="false"
        active-color="#2563eb"
        inactive-color="#64748b"
      >
        <van-tabbar-item :to="props.holdingLink" icon="plus">
          添加持仓
        </van-tabbar-item>
        <van-tabbar-item :to="props.actionLink" icon="records">
          添加流水
        </van-tabbar-item>
      </van-tabbar>
    </template>
    <van-button v-else type="primary" block round :to="props.actionLink">添加流水</van-button>
  </div>
</template>
