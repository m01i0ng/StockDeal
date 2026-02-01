import { createRouter, createWebHashHistory } from "vue-router";

import HomeView from "../views/HomeView.vue";
import PositionsView from "../views/PositionsView.vue";
import WatchlistView from "../views/WatchlistView.vue";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
      meta: { title: "主页" },
    },
    {
      path: "/positions",
      name: "positions",
      component: PositionsView,
      meta: { title: "持仓" },
    },
    {
      path: "/watchlist",
      name: "watchlist",
      component: WatchlistView,
      meta: { title: "自选" },
    },
  ],
});

export default router;
