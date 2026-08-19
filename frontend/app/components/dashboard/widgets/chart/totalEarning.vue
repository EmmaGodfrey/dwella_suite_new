<template>
  <div class="col-xl-5">
    <div class="card o-hidden">
      <div class="card-header pb-0">
        <h5>Total Earning</h5>
      </div>
      <div class="bar-chart-widget">
        <div class="top-content bg-primary"></div>
        <div class="bottom-content card-body">
          <div class="row">
            <div class="col-12">
              <div id="chart-widget5">
                <ClientOnly>
                  <apexchart type="radialBar" height="315" ref="chart" :options="chartOptions" :series="series"></apexchart>
                </ClientOnly>
              </div>
            </div>
          </div>
          <div class="row text-center">
            <div class="col-4 b-r-light">
              <div>
                <span class="font-primary">12%<i class="icon-angle-up f-12 ms-1"></i></span><span class="text-muted block-bottom">Year</span>
                <h4 class="num m-0">
                  <span class="counter color-bottom"> <CommenNumberAnimations data="73" /> </span>M
                </h4>
              </div>
            </div>
            <div class="col-4 b-r-light">
              <div>
                <span class="font-primary">15%<i class="icon-angle-up f-12 ms-1"></i></span><span class="text-muted block-bottom">Month</span>
                <h4 class="num m-0">
                  <span class="counter color-bottom"> <CommenNumberAnimations data="13" /> </span>M
                </h4>
              </div>
            </div>
            <div class="col-4">
              <div>
                <span class="font-primary">34%<i class="icon-angle-up f-12 ms-1"></i></span><span class="text-muted block-bottom">Today</span>
                <h4 class="num m-0">
                  <span class="counter color-bottom"> <CommenNumberAnimations data="187" /> </span>M
                </h4>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const series = [70];
const chartOptions = {
  chart: {
    height: 350,
    type: 'radialBar',
  },
  plotOptions: {
    radialBar: {
      hollow: {
        margin: 15,
        size: '70%',
        image: '/images/email-template/success.png',
        imageWidth: 64,
        imageHeight: 64,
        imageClipped: false,
      },
      dataLabels: {
        name: {
          show: false,
          color: '#fff',
        },
        value: {
          show: true,
          color: '#333',
          offsetY: 70,
          fontSize: '22px',
        },
      },
    },
  },
  colors: ['#999999'],
  stroke: {
    lineCap: 'round',
  },
  labels: ['Volatility'],
};
</script>
