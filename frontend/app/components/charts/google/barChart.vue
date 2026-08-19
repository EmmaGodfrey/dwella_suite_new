<template>
  <div class="col-sm-12 col-xl-6 box-col-12">
    <div class="card">
      <div class="card-header">
        <h5>bar-chart2</h5>
      </div>
      <div class="card-body chart-block">
        <div id="bar-chart2">
          <client-only> <GChart class="chart-overflow" id="bar-chart2" type="BarChart" :data="barChart.chartData_1" :options="barChart.options_1" /></client-only>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const barChart = {
  chartData_1: [
    ['Element', 'Density', { role: 'style' }],
    ['Copper', 10, primary.value],
    ['Silver', 12, secondary.value],
    ['Gold', 14, '#222222'],
    ['Platinum', 16, 'color: #717171'],
  ],
  options_1: {
    title: 'Density of Precious Metals, in g/cm^3',
    width: '100%',
    height: 400,
    bar: { groupWidth: '95%' },
    legend: { position: 'none' },
  },
};
</script>
