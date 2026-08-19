<template>
  <ClientOnly>
    <apexchart type="bar" height="90" :series="series" :options="chartOptions" />
  </ClientOnly>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const series = [
  {
    name: 'Inflation',
    data: [2.3, 5.1, 3.0, 9.1, 2.0, 4.6, 2.2, 9.3, 5.4, 4.8, 3.5, 5.2, 2.3, 5.1, 3.0, 9.1, 2.0, 4.6, 2.2, 9.3, 5.4, 4.8, 3.5, 5.2],
  },
];
const chartOptions = {
  chart: {
    height: 90,
    type: 'bar',
    toolbar: {
      show: false,
    },
  },
  plotOptions: {
    bar: {
      dataLabels: {
        position: 'top',
      },

      columnWidth: '20%',
      startingShape: 'rounded',
      endingShape: 'rounded',
      colors: {
        backgroundBarColors: ['#d8e3e5'],
        backgroundBarOpacity: 1,
        backgroundBarRadius: 9,
      },
    },
  },
  dataLabels: {
    enabled: false,
    offsetY: -10,
    style: {
      fontSize: '12px',
      colors: ['#912efc'],
    },
  },
  xaxis: {
    categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    position: 'bottom',

    axisBorder: {
      show: false,
    },
    axisTicks: { show: false },
    crosshairs: {
      fill: {
        type: 'gradient',
        gradient: {
          colorFrom: primary.value,
          colorTo: '#c481ec',
          stops: [0, 100],
          opacityFrom: 0.4,
          opacityTo: 0.5,
        },
      },
    },
    tooltip: { enabled: true },
    labels: { show: false },
  },
  yaxis: {
    axisBorder: {
      show: false,
    },
    axisTicks: {
      show: false,
    },
    labels: {
      show: false,
    },
  },
  colors: [secondary.value],
};
</script>
