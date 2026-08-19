<template>
  <div class="col-sm-12 col-xl-6 box-col-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Area Spaline Chart</h5>
      </div>
      <div class="card-body">
        <div id="area-spaline">
          <ClientOnly>
            <apexchart type="area" height="350" ref="chart" :options="chartOptions" :series="series"> </apexchart>
          </ClientOnly>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const series = [
  {
    name: 'series1',
    data: [31, 40, 28, 51, 42, 109, 100],
  },
  {
    name: 'series2',
    data: [11, 32, 45, 32, 34, 52, 41],
  },
];
const chartOptions = {
  chart: {
    height: 350,
    type: 'area',
    toolbar: {
      show: false,
    },
  },
  dataLabels: {
    enabled: false,
  },
  stroke: {
    curve: 'smooth',
  },
  xaxis: {
    type: 'datetime',
    categories: ['2018-09-19T00:00:00', '2018-09-19T01:30:00', '2018-09-19T02:30:00', '2018-09-19T03:30:00', '2018-09-19T04:30:00', '2018-09-19T05:30:00', '2018-09-19T06:30:00'],
  },
  tooltip: {
    x: {
      format: 'dd/MM/yy HH:mm',
    },
  },
  colors: [primary.value, secondary.value],
};
</script>
