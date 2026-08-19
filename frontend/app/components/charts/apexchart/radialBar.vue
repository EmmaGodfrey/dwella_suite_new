<template>
  <div class="col-sm-12 col-xl-6 box-col-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Radial Bar Chart</h5>
      </div>
      <div class="card-body">
        <div id="circlechart">
          <ClientOnly>
            <apexchart height="350" type="radialBar" :options="chartOptions" :series="series"> </apexchart>
          </ClientOnly>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const series = [44, 55, 67, 83];
const chartOptions = {
  chart: {
    height: 350,
    type: 'radialBar',
  },
  plotOptions: {
    radialBar: {
      dataLabels: {
        name: {
          fontSize: '22px',
        },
        value: {
          fontSize: '16px',
        },
        total: {
          show: true,
          label: 'Total',
          formatter: function () {
            return 249;
          },
        },
      },
    },
  },
  responsive: [
    {
      breakpoint: 480,
      options: {
        chart: {
          height: 300,
        },
      },
    },
  ],
  labels: ['Apples', 'Oranges', 'Bananas', 'Berries'],
  colors: [primary.value, secondary.value, '#222222', '#717171'],
};
</script>
