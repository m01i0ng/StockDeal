import { defineStore } from "pinia";
import { ref } from "vue";

export const useAppStore = defineStore("app", () => {
  const fundCount = ref(6);

  return {
    fundCount,
  };
});
