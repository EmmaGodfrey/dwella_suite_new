<template>
  <div class="xl-50 col-xl-7 box-col-6">
    <div class="small-chart-widget chart-widgets-small">
      <div class="card">
        <div class="card-header pb-0">
          <h5>Uses</h5>
        </div>
        <div class="card-body">
          <div class="chart-container">
            <div class="row">
              <div class="col-12">
                <div id="chart-widget9">
                  <ClientOnly>
                    <apexchart type="bubble" height="320" :series="series" :options="chartOptions"> </apexchart>
                  </ClientOnly>
                </div>
              </div>
            </div>
          </div>
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
    data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
      min: 10,
      max: 60,
    }),
  },
  {
    name: 'Bubble2',
    data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
      min: 10,
      max: 60,
    }),
  },
  {
    name: 'Bubble3',
    data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
      min: 10,
      max: 60,
    }),
  },
  {
    name: 'Bubble4',
    data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
      min: 10,
      max: 60,
    }),
  },
];
const chartOptions = {
  chart: {
    toolbar: {
      show: false,
    },
    height: 320,
    type: 'bubble',
  },
  dataLabels: {
    enabled: false,
  },
  fill: {
    type: 'gradient',
    gradient: {
      shade: 'dark',
      type: 'horizontal',
      shadeIntensity: 0.4,
      inverseColors: false,
      opacityFrom: 1,
      opacityTo: 0.7,
      stops: [0, 100],
    },
  },
  colors: [primary.value, secondary.value, '#222222', '#e2c636'],
  xaxis: {
    tickAmount: 12,
    type: 'category',
  },
  yaxis: {
    max: 70,
  },
};
function generateData(baseval: number, count: number, yrange: { max: number; min: number }) {
  var i = 0;
  var series = [];
  while (i < count) {
    var x = Math.floor(Math.random() * (750 - 1 + 1)) + 1;
    var y = Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;
    var z = Math.floor(Math.random() * (75 - 15 + 1)) + 15;
    series.push([x, y, z]);
    baseval += 86400000;
    i++;
  }
  return series;
}
</script>
