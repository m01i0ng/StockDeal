<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const props = defineProps<{
  title: string;
}>();

const router = useRouter();
const route = useRoute();

const showBack = computed(() => route.path !== "/");

const handleBack = () => {
  router.back();
};
</script>

<template>
  <van-nav-bar
    :title="props.title"
    :left-text="showBack ? '返回' : undefined"
    :left-arrow="showBack"
    fixed
    safe-area-inset-top
    @click-left="handleBack"
  />
</template>
