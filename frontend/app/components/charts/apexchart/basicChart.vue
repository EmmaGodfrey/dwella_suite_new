<template>
  <div class="col-sm-12 col-xl-6 box-col-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Basic Area Chart</h5>
      </div>
      <div class="card-body">
        <div id="basic-apex">
          <ClientOnly>
            <apexchart type="area" height="350" ref="chart" :options="chartOptions" :series="series"> </apexchart>
          </ClientOnly>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { monthDataSeries1 } from '~/data/chart-data';
const primary = ref<string>(useCookie('primary_color').value || '#24695c');

const series = [
  {
    name: 'STOCK ABC',
    data: monthDataSeries1[0]!.prices,
  },
];
const chartOptions = {
  chart: {
    height: 350,
    type: 'area',
    zoom: {
      enabled: false,
    },
    toolbar: {
      show: false,
    },
  },
  dataLabels: {
    enabled: false,
  },
  stroke: {
    curve: 'straight',
  },
  title: {
    text: 'Fundamental Analysis of Stocks',
    align: 'left',
  },
  subtitle: {
    text: 'Price Movements',
    align: 'left',
  },
  labels: monthDataSeries1[0]!.dates,
  xaxis: {
    type: 'datetime',
  },
  yaxis: {
    opposite: true,
  },
  legend: {
    horizontalAlign: 'left',
  },
  colors: [primary.value],
};
</script>
