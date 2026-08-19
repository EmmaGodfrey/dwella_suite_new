<template>
  <div class="col-sm-12 col-xl-4 box-col-6">
    <div class="card">
      <div class="card-header">
        <h5>Pie Chart <span class="digits">4</span></h5>
      </div>
      <div class="card-body p-0 chart-block">
        <client-only> <GChart class="chart-overflow" id="pie-chart2" type="PieChart" :data="pieChart.chartData_1" :options="pieChart.options_2" /></client-only>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const pieChart = {
  chartData_1: [
    ['Task', 'Hours per Day'],
    ['Work', 5],
    ['Eat', 10],
    ['Commute', 15],
    ['Watch TV', 20],
    ['Sleep', 25],
  ],
  options_2: {
    title: 'My Daily Activities',
    pieHole: 0.4,
    width: '100%',
    height: 300,
    colors: [secondary.value, primary.value, '#222222', '#717171', '#e2c636'],
  },
};
</script>
