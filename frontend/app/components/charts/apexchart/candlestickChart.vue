<template>
  <div class="col-sm-12 col-xl-6 box-col-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Candlestick Chart</h5>
      </div>
      <div class="card-body">
        <div id="candlestick">
          <ClientOnly>
            <apexchart type="candlestick" height="350" ref="chart" :options="chartOptions" :series="series"> </apexchart>
          </ClientOnly>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { chartData } from '~/data/chart-data';

const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const series = [
  {
    data: chartData,
  },
];
const chartOptions = {
  chart: {
    height: 350,
    type: 'candlestick',
    toolbar: {
      show: false,
    },
  },
  plotOptions: {
    candlestick: {
      colors: {
        upward: primary.value,
        downward: secondary.value,
      },
    },
  },
  title: {
    text: 'CandleStick Chart',
    align: 'left',
  },
  xaxis: {
    type: 'datetime',
  },
  yaxis: {
    tooltip: {
      enabled: true,
    },
  },
  colors: ['#000000'],
};
</script>
