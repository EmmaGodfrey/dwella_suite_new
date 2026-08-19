<template>
  <ClientOnly>
    <apexchart type="line" height="450" :series="series" :options="chartOptions"></apexchart>
  </ClientOnly>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const series = [
  {
    name: 'Total Views',
    data: generateDayWiseTimeSeries(0, 18),
  },
  {
    name: 'Unique Views',
    data: generateDayWiseTimeSeries(1, 18),
  },
];
const chartOptions = {
  chart: {
    type: 'line',
    height: 450,
    foreColor: '#999',
    stacked: true,
    dropShadow: {
      enabled: true,
      enabledSeries: [0],
      top: -2,
      left: 2,
      blur: 5,
      opacity: 0.06,
    },
    toolbar: {
      show: false,
    },
  },
  responsive: [
    {
      breakpoint: 1470,
      options: {
        chart: {
          height: 440,
        },
      },
    },
    {
      breakpoint: 1365,
      options: {
        chart: {
          height: 300,
        },
      },
    },
    {
      breakpoint: 991,
      options: {
        chart: {
          height: 250,
        },
      },
    },
  ],
  colors: [primary.value, secondary.value],
  stroke: {
    width: 3,
  },
  dataLabels: {
    enabled: false,
  },

  markers: {
    size: 5,
    strokeColor: '#e3e3e3',
    strokeWidth: 3,
    strokeOpacity: 1,
    fillOpacity: 1,
    hover: {
      size: 6,
    },
  },
  xaxis: {
    type: 'datetime',
    axisBorder: {
      show: false,
    },
    axisTicks: {
      show: false,
    },
  },
  yaxis: {
    tooltip: {
      enabled: true,
    },
    labels: {
      offsetX: 14,
      offsetY: -5,
      formatter: function (value: number) {
        return value + 'k';
      },
    },
  },
  grid: {
    padding: {
      left: -5,
      right: 5,
    },
  },
  tooltip: {
    x: {
      format: 'dd MMM yyyy',
    },
  },
  legend: {
    position: 'top',
    horizontalAlign: 'left',
    show: false,
  },
  fill: {
    type: 'solid',
    fillOpacity: 0.7,
  },
};
function generateDayWiseTimeSeries(s: number, count: number): [number, number][] {
  const values: number[][] = [
    [4, 3, 10, 9, 29, 19, 25, 9, 12, 7, 19, 5, 13, 9, 17, 2, 7, 5],
    [2, 3, 8, 7, 22, 16, 23, 7, 11, 5, 12, 5, 10, 4, 15, 2, 6, 2],
  ];
  let i = 0;
  const series: [number, number][] = [];
  let x = new Date('11 Nov 2012').getTime();

  while (i < count) {
    series.push([x, values[s]![i]!]);
    x += 86400000; // add one day
    i++;
  }
  return series;
}
</script>
