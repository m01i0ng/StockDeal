<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import AppHeader from "./AppHeader.vue";
import AppTabbar from "./AppTabbar.vue";
import AppActionBar from "./AppActionBar.vue";

const route = useRoute();
const pageTitle = computed(() => (route.meta.title as string) ?? "基金管理");
const layout = computed(() => (route.meta.layout as string) ?? "tabbar");
const showTabbar = computed(() => layout.value === "tabbar");
const showActionBar = computed(() => layout.value === "action");
const actionLink = computed(() => {
  const accountId = route.params.id;
  if (typeof accountId === "string" && accountId.length > 0) {
    return { path: "/transactions/new", query: { account_id: accountId } };
  }
  return "/transactions/new";
});
const holdingLink = computed(() => {
  const accountId = route.params.id;
  if (typeof accountId === "string" && accountId.length > 0) {
    return { path: "/holdings/new", query: { account_id: accountId } };
  }
  return "/holdings/new";
});
const isAccountPage = computed(() => route.name === "account");
const contentClass = computed(() => ({
  "is-action": layout.value === "action",
  "is-compact": layout.value === "none",
}));
</script>

<template>
  <div class="app-shell">
    <AppHeader :title="pageTitle" />

    <main class="app-content" :class="contentClass">
      <router-view />
    </main>

    <AppTabbar v-if="showTabbar" />
    <AppActionBar
      v-if="showActionBar"
      :is-account-page="isAccountPage"
      :action-link="actionLink"
      :holding-link="holdingLink"
    />
  </div>
</template>
