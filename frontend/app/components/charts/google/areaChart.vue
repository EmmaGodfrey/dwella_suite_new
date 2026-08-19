<template>
  <div class="col-sm-12 col-xl-4 box-col-6">
    <div class="card">
      <div class="card-header">
        <h5>Area Chart <span>1</span></h5>
      </div>
      <div class="card-body p-0 chart-block">
        <client-only>
          <GChart class="chart-overflow" id="area-chart1" type="AreaChart" :data="areaChart.chartData_1" :options="areaChart.options_1" />
        </client-only>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-xl-4 box-col-6">
    <div class="card">
      <div class="card-header">
        <h5>Area Chart <span>2</span></h5>
      </div>
      <div class="card-body p-0 chart-block">
        <client-only>
          <GChart class="chart-overflow" id="area-chart2" type="AreaChart" :data="areaChart.chartData_2" :options="areaChart.options_2" />
        </client-only>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const areaChart = {
  chartData_1: [
    ['Year', 'Sales', 'Expenses'],
    ['2013', 1000, 400],
    ['2014', 1170, 460],
    ['2015', 660, 1120],
    ['2016', 1030, 540],
  ],
  chartData_2: [
    ['Year', 'Cars', 'Trucks', 'Drones', 'Segways'],
    ['2013', 100, 400, 2000, 400],
    ['2014', 500, 700, 530, 800],
    ['2015', 2000, 1000, 620, 120],
    ['2016', 120, 201, 2501, 540],
  ],
  options_1: {
    title: 'Company Performance',
    hAxis: { title: 'Year', titleTextStyle: { color: '#333' } },
    vAxis: { minValue: 0 },
    width: '100%',
    height: 400,
    colors: [primary.value, secondary.value],
  },
  options_2: {
    title: 'Company Performance',
    hAxis: { title: 'Year', titleTextStyle: { color: '#333' } },
    vAxis: { minValue: 0 },
    width: '100%',
    height: 400,
    colors: [primary.value, secondary.value, '#222222', '#717171'],
  },
};
</script>
