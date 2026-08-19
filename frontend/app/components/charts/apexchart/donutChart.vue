<template>
  <div class="col-sm-12 col-xl-6 box-col-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Donut Chart</h5>
      </div>
      <div class="card-body apex-chart">
        <div id="donutchart">
          <ClientOnly>
            <apexchart width="380" type="donut" :options="chartOptions" :series="series" :responsive="chartOptions.responsive"></apexchart>
          </ClientOnly>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');

const series = [44, 55, 41, 17, 15];
const chartOptions = {
  chart: {
    width: 380,
    height: 380,
    type: 'donut',
  },
  responsive: [
    {
      breakpoint: 480,
      options: {
        chart: {
          width: 300,
        },
        legend: {
          position: 'bottom',
        },
      },
    },
  ],
  colors: [primary.value, secondary.value, '#222222', '#717171', '#e2c636'],
};
</script>
