import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import { setupApiInterceptors } from "./api/setup";
import "./style.css";

const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

const applySystemTheme = (isDark: boolean) => {
  const root = document.documentElement;
  root.classList.toggle("dark", isDark);
  root.classList.toggle("van-theme-dark", isDark);
  root.classList.toggle("van-theme-light", !isDark);
};

applySystemTheme(darkQuery.matches);
darkQuery.addEventListener("change", (event) => {
  applySystemTheme(event.matches);
});

setupApiInterceptors();

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
