<template>
  <ClientOnly>
    <apexchart type="bar" height="265" :series="series" :options="chartOptions"></apexchart>
  </ClientOnly>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const series = [
  {
    name: 'Yearly Profit',
    data: [
      {
        x: 'Jan',
        y: 1500,
        fillColor: primary.value,
      },
      {
        x: 'Feb',
        y: 3000,
        fillColor: primary.value,
      },
      {
        x: 'Mar',
        y: 1800,
        fillColor: primary.value,
      },
      {
        x: 'Apr',
        y: 3000,
        fillColor: secondary.value,
      },
      {
        x: 'May',
        y: 1800,
        fillColor: primary.value,
      },
      {
        x: 'Jun',
        y: 1500,
        fillColor: primary.value,
      },
      {
        x: 'Jul',
        y: 2500,
        fillColor: primary.value,
      },
      {
        x: 'Sep',
        y: 1500,
        fillColor: secondary.value,
      },
      {
        x: 'Oct',
        y: 2000,
        fillColor: primary.value,
      },
    ],
  },
];
const chartOptions = {
  chart: {
    height: 250,
    width: 60,
    type: 'bar',
    toolbar: { show: false },
  },
  plotOptions: {
    bar: {
      horizontal: false,
      columnWidth: '20',
      e̶n̶d̶i̶n̶g̶S̶h̶a̶p̶e̶: 'rounded',
      borderRadius: 7,
      colors: {
        backgroundBarColors: ['#e5edef'],
        backgroundBarOpacity: 1,
        backgroundBarRadius: 8,
      },
    },
  },
  stroke: { show: false },
  dataLabels: { enabled: false },
  fill: { opacity: 1 },
  xaxis: {
    axisBorder: {
      show: false,
    },
    labels: {
      show: true,
    },
    axisTicks: {
      show: false,
    },
  },
  yaxis: {
    labels: { show: false },
  },
};
</script>
