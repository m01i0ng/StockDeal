<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const pageTitle = computed(() => (route.meta.title as string) ?? "基金管理");
</script>

<template>
  <div class="app-shell">
    <van-nav-bar :title="pageTitle" fixed safe-area-inset-top />

    <main class="app-content">
      <router-view />
    </main>

    <van-tabbar route fixed>
      <van-tabbar-item to="/" icon="home-o">主页</van-tabbar-item>
      <van-tabbar-item to="/positions" icon="chart-trending-o">
        持仓
      </van-tabbar-item>
      <van-tabbar-item to="/watchlist" icon="star-o">自选</van-tabbar-item>
    </van-tabbar>
  </div>
</template>
