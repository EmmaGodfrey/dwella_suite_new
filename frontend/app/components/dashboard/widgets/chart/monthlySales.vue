<template>
  <div class="xl-50 col-xl-5 box-col-6">
    <div class="small-chart-widget chart-widgets-small">
      <div class="card">
        <div class="card-header pb-0">
          <h5>Monthly Sales</h5>
          <div class="card-body">
            <div class="chart-container">
              <div class="row">
                <div class="col-12">
                  <div id="chart-widget8">
                    <ClientOnly>
                      <apexchart type="radar" height="310" ref="chart" :options="chartOptions" :series="series"></apexchart>
                    </ClientOnly>
                  </div>
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
    name: 'Series 1',
    data: [80, 50, 30, 40, 100, 20],
  },
  {
    name: 'Series 2',
    data: [20, 30, 40, 80, 20, 80],
  },
  {
    name: 'Series 3',
    data: [44, 76, 78, 13, 43, 10],
  },
];
const chartOptions = {
  fill: {
    type: 'gradient',
    gradient: {
      shade: 'dark',
      type: 'Reflected',
      shadeIntensity: 0.1,
      inverseColors: false,
      opacityFrom: 1,
      opacityTo: 0.8,
      stops: [0, 100],
    },
  },
  colors: [primary.value, secondary.value, '#e2c636'],
  chart: {
    height: 320,
    type: 'radar',
    dropShadow: {
      enabled: true,
      blur: 1,
      left: 1,
      top: 1,
    },
  },

  stroke: {
    width: 0,
  },
  markers: {
    size: 0,
  },
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
};
</script>
