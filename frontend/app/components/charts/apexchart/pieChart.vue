<template>
  <div class="col-sm-12 col-xl-6 box-col-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Pie Chart</h5>
      </div>
      <div class="card-body apex-chart">
        <div id="piechart">
          <ClientOnly>
            <apexchart width="380" type="pie" :options="chartOptions" :series="series" :responsive="chartOptions.responsive"></apexchart>
          </ClientOnly>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const series = [44, 55, 13, 43, 22];
const chartOptions = {
  chart: {
    width: 380,

    type: 'pie',
  },
  labels: ['Team A', 'Team B', 'Team C', 'Team D', 'Team E'],
  responsive: [
    {
      breakpoint: 480,
      options: {
        chart: {
          width: 280,
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
