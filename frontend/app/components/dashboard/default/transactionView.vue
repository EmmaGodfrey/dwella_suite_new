<template>
  <div class="col-xl-12 box-col-6 des-xl-50">
    <div class="card trasaction-sec overflow-hidden">
      <div class="card-header">
        <div class="header-top d-sm-flex align-items-center">
          <h5>Transaction</h5>
          <div class="center-content">
            <p>5878 Suceessfull Transaction</p>
          </div>
        </div>
      </div>
      <div class="transaction-totalbal">
        <h2>
          $2,09,352k
          <span class="ms-3">
            <a class="btn-arrow arrow-secondary" href="javascript:void(0)"> <i class="toprightarrow-secondary fa fa-arrow-up me-2 d-grid"></i>98.54%</a>
          </span>
        </h2>
        <p>Total Balance</p>
      </div>
      <div class="card-body p-0">
        <div id="chart-3dash">
          <ClientOnly>
            <apexchart type="area" height="405" :series="series" :options="chartOptions"></apexchart>
          </ClientOnly>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const series = [
  {
    name: 'series1',
    data: [90, 78, 90, 84, 94, 60, 95, 88, 95],
  },
];
const chartOptions = {
  chart: {
    height: 405,
    type: 'area',
    toolbar: {
      show: false,
    },
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
    labels: {
      show: false,
    },
    axisTicks: {
      show: false,
    },
  },
  tooltip: {
    x: {
      format: 'dd/MM/yy HH:mm',
      enabled: false,
    },
  },
  colors: [secondary.value],
  responsive: [
    {
      breakpoint: 1365,
      options: {
        chart: {
          height: 220,
        },
      },
    },
    {
      breakpoint: 575,
      options: {
        chart: {
          height: 180,
        },
      },
    },
    {
      breakpoint: 992,
      options: {
        chart: {
          height: 250,
        },
      },
    },
  ],
};
</script>
