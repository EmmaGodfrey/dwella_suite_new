<template>
  <div class="col-sm-12 box-col-12">
    <div class="card">
      <div class="card-header">
        <h5>Line Chart</h5>
      </div>
      <div class="card-body chart-block">
        <client-only> <GChart class="chart-overflow" id="line-chart" type="LineChart" :data="lineChart.chartData_1" :options="lineChart.options_1" /></client-only>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const lineChart = {
  chartData_1: [
    ['Month', 'Guardians of the Galaxy', 'The Avengers', 'Transformers: Age of Extinction'],
    [1, 37.8, 80.8, 41.8],
    [2, 30.9, 10.5, 32.4],
    [3, 40.4, 57, 25.7],
    [4, 11.7, 18.8, 10.5],
    [5, 20, 17.6, 10.4],
    [6, 8.8, 13.6, 7.7],
    [7, 7.6, 12.3, 9.6],
    [8, 12.3, 29.2, 10.6],
    [9, 16.9, 42.9, 14.8],
    [10, 12.8, 30.9, 11.6],
    [11, 5.3, 7.9, 4.7],
    [12, 6.6, 8.4, 5.2],
  ],
  options_1: {
    chart: {
      title: 'Box Office Earnings in First Two Weeks of Opening',
      subtitle: 'in millions of dollars (USD)',
    },
    colors: [primary.value, secondary.value, '#222222'],
    height: 500,
    width: '100%',
  },
};
</script>
