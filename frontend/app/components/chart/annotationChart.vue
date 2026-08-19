<template>
  <ClientOnly>
    <apexchart type="line" height="350" ref="chart" :options="chartOptions" :series="series"></apexchart>
  </ClientOnly>
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
  annotations: {
    yaxis: [
      {
        y: 8200,
        borderColor: '#00E396',
        label: {
          borderColor: '#00E396',
          style: {
            color: '#fff',
            background: '#00E396',
          },
          text: 'Support',
        },
      },
      {
        y: 8600,
        y2: 9000,
        borderColor: '#000',
        fillColor: '#FEB019',
        opacity: 0.2,
        label: {
          borderColor: '#333',
          style: { fontSize: '10px', color: '#333', background: '#FEB019' },
          text: 'Y-axis range',
        },
      },
    ],
    xaxis: [
      {
        x: new Date('23 Nov 2017').getTime(),
        strokeDashArray: 0,
        borderColor: '#775DD0',
        label: {
          borderColor: '#775DD0',
          style: {
            color: '#fff',
            background: '#775DD0',
          },
          text: 'Anno Test',
        },
      },
      {
        x: new Date('26 Nov 2017').getTime(),
        x2: new Date('28 Nov 2017').getTime(),
        fillColor: '#B3F7CA',
        opacity: 0.4,
        label: {
          borderColor: '#B3F7CA',
          style: {
            fontSize: '10px',
            color: '#fff',
            background: '#00E396',
          },
          offsetY: -10,
          text: 'X-axis range',
        },
      },
    ],
    points: [
      {
        x: new Date('01 Dec 2017').getTime(),
        y: 8607.55,
        marker: {
          size: 8,
          fillColor: '#fff',
          strokeColor: 'red',
          radius: 2,
          cssClass: 'apexcharts-custom-class',
        },
        label: {
          borderColor: '#FF4560',
          offsetY: 0,
          style: {
            color: '#fff',
            background: '#FF4560',
          },
          text: 'Point Annotation',
        },
      },
    ],
  },
  chart: {
    height: 350,
    type: 'line',
    id: 'areachart-2',
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
  grid: {
    padding: {
      right: 30,
      left: 20,
    },
  },
  labels: monthDataSeries1[0]!.dates,
  title: {
    text: 'Line with Annotations',
    align: 'left',
  },
  xaxis: {
    type: 'datetime',
  },
  colors: [primary.value],
};
</script>
