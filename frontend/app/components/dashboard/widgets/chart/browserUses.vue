<template>
  <div class="col-sm-12 box-col-12">
    <div class="donut-chart-widget">
      <div class="card">
        <div class="card-header pb-0">
          <h5>Browser Uses</h5>
        </div>
        <div class="card-body">
          <div id="chart-widget13">
            <ClientOnly>
              <apexchart type="candlestick" height="500" :series="series" :options="chartOptions"> </apexchart>
            </ClientOnly>
          </div>
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
    toolbar: {
      show: false,
    },
    width: 855,
    height: 320,
    type: 'candlestick',
  },
  plotOptions: {
    candlestick: {
      colors: {
        upward: primary.value,
        downward: secondary.value,
      },
    },
  },
  fill: {
    opacity: 0.9,
    colors: ['#fb2e63'],
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
};
</script>
