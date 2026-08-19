<template>
  <div class="col-sm-12 col-xl-6 box-col-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Stepline Chart</h5>
      </div>
      <div class="card-body">
        <div id="stepline">
          <ClientOnly>
            <apexchart height="350" type="line" :options="chartOptions" :series="series"></apexchart>
          </ClientOnly>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');

const series = [
  {
    data: [34, 44, 54, 21, 12, 43, 33, 23, 66, 66, 58],
  },
];
const chartOptions = {
  chart: {
    type: 'line',
    height: 350,
    toolbar: {
      show: false,
    },
  },
  stroke: {
    curve: 'stepline',
  },
  dataLabels: {
    enabled: false,
  },
  title: {
    text: 'Stepline Chart',
    align: 'left',
  },
  markers: {
    hover: {
      sizeOffset: 4,
    },
  },
  colors: [primary.value],
};
</script>
