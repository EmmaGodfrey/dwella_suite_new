<template>
  <div class="col-xl-4">
    <div class="card o-hidden">
      <div class="chart-widget-top">
        <div class="row card-body">
          <div class="col-5">
            <h6 class="f-w-600 font-primary sales">SALE</h6>
            <span class="num sales"
              ><span class="counter"> <CommenNumberAnimations data="90" /> </span>%<i class="icon-angle-up f-12"></i
            ></span>
          </div>
          <div class="col-7 text-end">
            <h4 class="num total-value">
              $
              <span class="counter"> <CommenNumberAnimations data="3654" /> </span>.00
            </h4>
          </div>
        </div>
        <div>
          <div id="chart-widget1">
            <ClientOnly>
              <apexchart type="area" height="180" ref="chart" :options="chartOptions" :series="series"> </apexchart>
            </ClientOnly>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');

const series = [
  {
    data: [1.2, 2.3, 1.7, 3.2, 1.8, 3.2, 1],
  },
];
const chartOptions = {
  chart: {
    toolbar: { show: false },
    height: 170,
    type: 'area',
  },
  dataLabels: { enabled: false },
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
      bottom: -15,
    },
  },
  fill: {
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
