import { createRouter, createWebHashHistory } from "vue-router";

import HomeView from "../views/HomeView.vue";
import PositionsView from "../views/PositionsView.vue";
import WatchlistView from "../views/WatchlistView.vue";
import AccountView from "../views/AccountView.vue";
import AccountNewView from "../views/AccountNewView.vue";
import TransactionNewView from "../views/TransactionNewView.vue";
import HoldingNewView from "../views/HoldingNewView.vue";
import HoldingDetailView from "../views/HoldingDetailView.vue";

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
      meta: { title: "持仓管理" },
    },
    {
      path: "/accounts/new",
      name: "account-new",
      component: AccountNewView,
      meta: { title: "新建账户", layout: "none" },
    },
    {
      path: "/accounts/:id",
      name: "account",
      component: AccountView,
      meta: { title: "账户详情", layout: "action" },
    },
    {
      path: "/holdings/new",
      name: "holding-new",
      component: HoldingNewView,
      meta: { title: "添加持仓", layout: "none" },
    },
    {
      path: "/holdings/:id",
      name: "holding-detail",
      component: HoldingDetailView,
      meta: { title: "持仓详情", layout: "none" },
    },
    {
      path: "/transactions/new",
      name: "transaction-new",
      component: TransactionNewView,
      meta: { title: "添加流水", layout: "none" },
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
