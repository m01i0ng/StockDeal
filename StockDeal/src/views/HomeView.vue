<script setup lang="ts">
import { computed } from "vue";
import { useAppStore } from "../stores/app";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from "echarts/components";
import VChart from "vue-echarts";

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent]);

const appStore = useAppStore();

const chartOption = computed(() => ({
  tooltip: {
    trigger: "axis",
  },
  legend: {
    data: ["预估净值"],
    bottom: 0,
  },
  grid: {
    left: 12,
    right: 12,
    top: 12,
    bottom: 36,
    containLabel: true,
  },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: ["09:30", "10:30", "11:30", "13:30", "14:30", "15:00"],
  },
  yAxis: {
    type: "value",
    axisLabel: {
      formatter: "{value}%",
    },
  },
  series: [
    {
      name: "预估净值",
      type: "line",
      smooth: true,
      data: [0.2, 0.35, 0.18, 0.46, 0.62, 0.48],
      areaStyle: {
        opacity: 0.12,
      },
    },
  ],
}));
</script>

<template>
  <section class="page-section">
    <header class="page-header">
      <div>
        <p class="page-kicker">基金管理</p>
        <h1 class="page-title">主页概览</h1>
      </div>
      <van-tag type="primary" round>运行中</van-tag>
    </header>

    <van-cell-group inset>
      <van-cell title="当前基金数" :value="appStore.fundCount" />
      <van-cell title="今日净值估算" value="+1.38%" />
      <van-cell title="累计收益" value="+12.6%" />
    </van-cell-group>

    <div class="page-block">
      <van-card title="预估净值走势" desc="近一日走势" class="chart-card">
        <template #tags>
          <van-tag plain type="primary">示例</van-tag>
        </template>
        <template #footer>
          <VChart class="chart-panel" :option="chartOption" autoresize />
        </template>
      </van-card>

      <van-card
        title="收益概览"
        desc="近 7 日波动"
        thumb="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
      >
        <template #tags>
          <van-tag plain type="success">稳健</van-tag>
        </template>
      </van-card>
    </div>
  </section>
</template>
