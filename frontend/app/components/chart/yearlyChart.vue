<template>
  <ClientOnly>
    <apexchart type="bar" height="356" ref="chart" :options="chartOptions" :series="series"></apexchart>
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
        x: '2001',
        y: 5500,
      },
      {
        x: '2002',
        y: 3800,
      },
      {
        x: '2003',
        y: 5500,
      },
      {
        x: '2004',
        y: 7700,
      },
      {
        x: '2005',
        y: 1500,
      },
      {
        x: '2006',
        y: 1000,
        fillColor: primary.value,
      },
      {
        x: '2007',
        y: 5000,
        fillColor: primary.value,
      },
      {
        x: '2008',
        y: 6000,
        fillColor: primary.value,
      },
      {
        x: '2009',
        y: 7900,
        fillColor: primary.value,
      },
      {
        x: '2010',
        y: 4700,
        fillColor: primary.value,
      },
      {
        x: '2011',
        y: 4000,
        fillColor: primary.value,
      },
      {
        x: '2012',
        y: 5000,
        fillColor: primary.value,
      },
      {
        x: '2013',
        y: 7500,
      },
      {
        x: '2014',
        y: 3500,
      },
      {
        x: '2015',
        y: 4000,
      },
      {
        x: '2016',
        y: 6500,
      },
      {
        x: '2017',
        y: 4000,
      },
      {
        x: '2018',
        y: 5853,
      },
      {
        x: '2019',
        y: 6553,
      },
      {
        x: '2020',
        y: 5200,
      },
      {
        x: '2021',
        y: 6200,
      },
      {
        x: '2022',
        y: 880,
        fillColor: secondary.value,
      },
      {
        x: '2023',
        y: 1200,
        fillColor: secondary.value,
      },
      {
        x: '2024',
        y: 8010,
        fillColor: secondary.value,
      },
      {
        x: '2025',
        y: 6053,
        fillColor: secondary.value,
      },
      {
        x: '2026',
        y: 4000,
        fillColor: secondary.value,
      },
      {
        x: '2027',
        y: 1000,
        fillColor: secondary.value,
      },
      {
        x: '2028',
        y: 6200,
      },
      {
        x: '2029',
        y: 6200,
      },
      {
        x: '2030',
        y: 7500,
      },
      {
        x: '2031',
        y: 7000,
      },
      {
        x: '2032',
        y: 5000,
      },
      {
        x: '2033',
        y: 6000,
      },
      {
        x: '2034',
        y: 8000,
      },
      {
        x: '2035',
        y: 4000,
      },
      {
        x: '2036',
        y: 4500,
      },
      {
        x: '2037',
        y: 4800,
      },
      {
        x: '2038',
        y: 3000,
        fillColor: secondary.value,
      },
      {
        x: '2039',
        y: 4200,
        fillColor: secondary.value,
      },
      {
        x: '2040',
        y: 7900,
        fillColor: secondary.value,
      },
      {
        x: '2041',
        y: 4000,
        fillColor: secondary.value,
      },
      {
        x: '2042',
        y: 5500,
        fillColor: secondary.value,
      },
      {
        x: '2043',
        y: 1000,
      },
      {
        x: '2044',
        y: 5500,
      },
      {
        x: '2045',
        y: 7000,
      },
      {
        x: '2046',
        y: 6500,
      },
      {
        x: '2047',
        y: 4000,
      },
    ],
  },
];
const chartOptions = {
  chart: {
    height: 350,
    type: 'bar',
    toolbar: {
      show: false,
    },
  },
  plotOptions: {
    bar: {
      horizontal: false,
      columnWidth: '70%',
    },
  },
  stroke: {
    show: false,
  },
  dataLabels: {
    enabled: false,
  },
  fill: {
    opacity: 1,
  },
  xaxis: {
    type: 'datetime',
    axisBorder: {
      show: false,
    },
    labels: {
      show: false,
    },
    axisTicks: {
      show: false,
    },
  },
  yaxis: {
    labels: {
      formatter: function (val: number) {
        return val / 100 + 'K';
      },
    },
  },
  responsive: [
    {
      breakpoint: 991,
      options: {
        chart: {
          height: 250,
        },
      },
    },
  ],
  colors: ['#d8e3e5'],
};
</script>
