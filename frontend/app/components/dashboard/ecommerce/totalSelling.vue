<template>
  <div class="col-xl-6 box-col-6">
    <div class="card">
      <div class="card-header">
        <div class="header-top d-sm-flex justify-content-between align-items-center">
          <h5>Total Selling</h5>
          <div class="center-content">
            <ul class="week-date">
              <li class="font-primary">Today</li>
              <li>Month</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="card-body chart-block p-0">
        <div id="chart-dash-2-line">
          <ClientOnly>
            <apexchart type="line" height="470" :series="series" :options="chartOptions"></apexchart>
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
    name: 'TEAM A',
    type: 'area',
    data: [44, 48, 38, 47],
  },
  {
    name: 'TEAM B',
    type: 'line',
    data: [42, 38, 48, 30],
  },
];
const chartOptions = {
  chart: {
    height: 470,
    type: 'line',
    toolbar: {
      show: false,
    },
  },
  stroke: {
    curve: 'smooth',
    width: [5, 2],
    dashArray: [0, 8],
  },
  fill: {
    type: 'solid',
    opacity: [0.35, 1],
  },
  labels: ['2010', '2011', '2012', '2013'],
  markers: {
    size: 5,
  },
  responsive: [
    {
      breakpoint: 991,
      options: {
        chart: { height: 300 },
      },
    },
    {
      breakpoint: 1500,
      options: {
        chart: { height: 325 },
      },
    },
  ],
  yaxis: [
    {
      labels: {
        formatter: function (value: number) {
          return value + 'k';
        },
      },
    },
  ],
  tooltip: {
    shared: true,
    intersect: false,
    y: {
      formatter: function (y: number) {
        if (typeof y !== 'undefined') {
          return y.toFixed(0) + ' points';
        }
        return y;
      },
    },
  },
  colors: [primary.value, secondary.value],
  legend: {
    show: false,
  },
};
</script>
