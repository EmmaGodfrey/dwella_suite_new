<template>
  <div class="col-sm-12 col-xl-6 box-col-6">
    <div class="card">
      <div class="card-header">
        <h5>Column Chart <span class="digits">1 </span></h5>
      </div>
      <div class="card-body chart-block">
        <client-only>
          <GChart
            class="chart-overflow"
            type="ColumnChart"
            id="column-chart1"
            :settings="{ packages: ['corechart'] }"
            :data="areaChart.chartData_1"
            :options="verticalChartOptions"
            :createChart="(el, google) => new google.visualization.ColumnChart(el)"
            @ready="onChartReady"
        /></client-only>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-xl-6 box-col-6">
    <div class="card">
      <div class="card-header">
        <h5>Column Chart <span class="digits">2</span></h5>
      </div>
      <div class="card-body chart-block">
        <client-only>
          <GChart
            class="chart-overflow"
            id="column-chart2"
            type="ColumnChart"
            :settings="{ packages: ['corechart'] }"
            :data="areaChart.chartData_1"
            :options="horizontalChartOptions"
            :createChart="(el, google) => new google.visualization.BarChart(el)"
            @ready="onChartReady"
        /></client-only>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { GChart } from 'vue-google-charts';

type GoogleLib = typeof google;
const chartsLib = ref<GoogleLib | null>(null);
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');

interface GoogleChartOptions {
  title?: string;
  subtitle?: string;
  bars?: 'vertical' | 'horizontal';
  vAxis?: { format?: string };
  hAxis?: { format?: string };
  height?: number;
  width?: number;
  colors?: string[];
}

const areaChart = {
  chartData_1: [
    ['Year', 'Sales', 'Expenses', 'Profit'],
    ['2014', 1e3, 400, 250],
    ['2015', 1170, 460, 300],
    ['2016', 660, 1120, 400],
    ['2017', 1030, 540, 450],
  ],
};
const verticalChartOptions = computed<GoogleChartOptions>(() => {
  if (!chartsLib.value) return {};
  return {
    title: 'Company Performance',
    subtitle: 'Sales, Expenses, and Profit: 2014-2017',
    bars: 'vertical',
    vAxis: { format: 'decimal' },
    height: 400,
    colors: [primary.value, secondary.value, '#61ae41'],
  };
});
const horizontalChartOptions = computed<GoogleChartOptions>(() => {
  if (!chartsLib.value) return {};
  return {
    title: 'Company Performance',
    subtitle: 'Sales, Expenses, and Profit: 2014-2017',
    bars: 'horizontal',
    vAxis: { format: 'decimal' },
    height: 400,
    colors: [primary.value, secondary.value, '#61ae41'],
  };
});
function onChartReady(google: GoogleLib) {
  chartsLib.value = google;
}
</script>
