<template>
  <div class="xl-50 col-xl-7 box-col-6">
    <div class="small-chart-widget chart-widgets-small">
      <div class="card">
        <div class="card-header pb-0">
          <h5>Live Products</h5>
        </div>
        <div class="card-body">
          <div class="chart-container">
            <div class="row">
              <div class="col-12">
                <div id="chart-widget6">
                  <ClientOnly>
                    <apexchart type="line" height="320" ref="chart" :options="chartOptions" :series="series"></apexchart>
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
    name: 'TEAM A',
    type: 'area',
    data: [44, 55, 31, 47, 31, 43, 26, 41, 31, 47, 33],
  },
  {
    name: 'TEAM B',
    type: 'line',
    data: [55, 69, 45, 61, 43, 54, 37, 52, 44, 61, 43],
  },
];
const chartOptions = {
  chart: {
    height: 320,
    type: 'line',
  },
  stroke: {
    curve: 'smooth',
  },

  fill: {
    colors: [primary.value, secondary.value],
    type: 'gradient',
    gradient: {
      shade: 'light',
      type: 'vertical',
      shadeIntensity: 0.4,
      inverseColors: false,
      opacityFrom: 0.9,
      opacityTo: 0.8,
      stops: [0, 100],
    },
  },
  colors: [primary.value, secondary.value],
  labels: ['01', '02', '03', '04', '05', '06', '07', '08', '09 ', '10', '11', '12'],
  markers: {
    size: 0,
  },
  yaxis: [
    {
      title: {
        text: 'Series A',
      },
    },
    {
      opposite: true,
      title: {
        text: 'Series B',
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
};
</script>
