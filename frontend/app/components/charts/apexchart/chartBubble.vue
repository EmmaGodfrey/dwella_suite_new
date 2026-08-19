<template>
  <div class="col-sm-12 col-xl-6 box-col-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>3d Bubble Chart</h5>
      </div>
      <div class="card-body">
        <div id="chart-bubble">
          <ClientOnly>
            <apexchart type="bubble" height="350" ref="chart" :options="chartOptions" :series="series"> </apexchart>
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
    name: 'Bubble1',
    data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, { min: 10, max: 60 }),
  },
  {
    name: 'Bubble2',
    data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, { min: 10, max: 60 }),
  },
  {
    name: 'Bubble3',
    data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, { min: 10, max: 60 }),
  },
  {
    name: 'Bubble4',
    data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, { min: 10, max: 60 }),
  },
];
const chartOptions = {
  chart: {
    height: 350,
    type: 'bubble',
    toolbar: {
      show: false,
    },
  },
  dataLabels: {
    enabled: false,
  },

  fill: {
    type: 'gradient',
  },
  title: {
    text: '3D Bubble Chart',
  },
  xaxis: {
    tickAmount: 12,
    type: 'datetime',

    labels: {
      rotate: 0,
    },
  },
  yaxis: {
    max: 70,
  },
  theme: {
    palette: 'palette2',
  },
  stroke: {
    width: 0,
  },
  colors: [primary.value, secondary.value, '#222222', '#717171'],
};
function generateData(baseval: number, count: number, yrange: { min: number; max: number }): [number, number, number][] {
  var i = 0;
  var series: [number, number, number][] = [];
  while (i < count) {
    var y = Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;
    var z = Math.floor(Math.random() * (75 - 15 + 1)) + 15;
    series.push([baseval, y, z]);
    baseval += 86400000;
    i++;
  }
  return series;
}
</script>
