<template>
  <ClientOnly>
    <apexchart type="area" height="425" ref="chart" :options="chartOptions" :series="series"></apexchart>
  </ClientOnly>
</template>
<script lang="ts" setup>
import { salesChart } from '~/data/chart-data';

const primary = ref<string>(useCookie('primary_color').value || '#24695c');

const series = [{ data: salesChart }];

const chartOptions = {
  chart: {
    id: 'area-datetime',
    type: 'area',
    height: 425,
    zoom: { autoScaleYaxis: true },
    toolbar: { show: false },
  },
  annotations: {
    yaxis: [
      {
        y: 50,
        borderColor: primary.value,
        label: {
          show: true,
          text: 'Support',
          style: { color: '#fff', background: primary.value },
        },
      },
    ],
    xaxis: [
      {
        x: new Date('15 Nov 2012').getTime(),
        borderColor: primary.value,
        yAxisIndex: 50,
        label: {
          show: false,
          text: '$859,432',
          style: { color: '#fff', background: primary.value },
        },
      },
    ],
  },
  dataLabels: { enabled: false },
  markers: { size: 0, style: 'hollow' },
  xaxis: {
    type: 'datetime',
    min: new Date('01 Apr 2012').getTime(),
    tickAmount: 6,
    axisTicks: { show: false },
    axisBorder: { show: false },
  },
  tooltip: {
    x: { format: 'dd MMM yyyy' },
  },
  fill: {
    type: 'gradient',
    gradient: { shadeIntensity: 1, opacityFrom: 0.7, opacityTo: 0.9, stops: [0, 100] },
  },
  responsive: [
    {
      breakpoint: 1366,
      options: {
        chart: { height: 350 },
      },
    },
    {
      breakpoint: 1238,
      options: {
        chart: { height: 300 },
        grid: {
          padding: { bottom: 5 },
        },
      },
    },
    {
      breakpoint: 992,
      options: {
        chart: { height: 300 },
      },
    },
    {
      breakpoint: 551,
      options: {
        grid: {
          padding: { bottom: 10 },
        },
      },
    },
    {
      breakpoint: 535,
      options: {
        chart: { height: 250 },
      },
    },
  ],
  colors: [primary.value],
};
</script>
