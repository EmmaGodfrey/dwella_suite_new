<template>
  <div class="col-xl-4">
    <div class="card o-hidden">
      <div class="chart-widget-top">
        <div class="row card-body">
          <div class="col-8">
            <h6 class="f-w-600 font-success sales">PRODUCTS</h6>
            <span class="num sales"
              ><span class="counter"> <CommenNumberAnimations data="68" /> </span>%<i class="icon-angle-up f-12"></i
            ></span>
          </div>
          <div class="col-4 text-end">
            <h4 class="num total-value">
              <span class="counter"> <CommenNumberAnimations data="93" /> </span>M
            </h4>
          </div>
        </div>
        <div id="chart-widget3">
          <div class="flot-chart-placeholder" id="chart-widget-top-third"></div>
          <ClientOnly>
            <apexchart type="area" height="180" ref="chart" :options="chartOptions" :series="series"> </apexchart>
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
    data: [24, 55, 21, 67, 22, 43, 21],
  },
];
const chartOptions = {
  chart: {
    toolbar: {
      show: false,
    },
    height: 170,
    type: 'area',
  },
  dataLabels: {
    enabled: false,
  },
  stroke: {
    curve: 'smooth',
  },
  yaxis: {
    show: false,
  },
  xaxis: {
    show: false,
    type: 'datetime',
    categories: ['2018-09-19T00:00:00', '2018-09-19T01:30:00', '2018-09-19T02:30:00', '2018-09-19T03:30:00', '2018-09-19T04:30:00', '2018-09-19T05:30:00', '2018-09-19T06:30:00'],
    labels: {
      show: false,
    },
    axisBorder: {
      show: false,
    },
  },
  grid: {
    show: false,
    padding: {
      left: 0,
      right: 0,
      bottom: -40,
    },
  },
  fill: {
    colors: [primary.value],
    type: 'gradient',
    gradient: {
      shade: 'light',
      type: 'vertical',
      shadeIntensity: 0.4,
      inverseColors: false,
      opacityFrom: 0.8,
      opacityTo: 0.2,
      stops: [0, 100],
    },
  },
  colors: [primary.value],

  tooltip: {
    x: {
      format: 'dd/MM/yy HH:mm',
      enabled: false,
    },
  },
};
</script>
