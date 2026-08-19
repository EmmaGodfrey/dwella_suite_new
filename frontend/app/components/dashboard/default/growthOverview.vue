<template>
  <div class="col-xl-8 box-col-12 des-xl-100">
    <div class="row">
      <div class="col-xl-6 col-50 box-col-6 des-xl-50">
        <div class="card">
          <div class="card-header">
            <div class="header-top d-sm-flex align-items-center">
              <h5>Growth Overview</h5>
              <div class="center-content">
                <p class="d-flex align-items-center"><i class="toprightarrow-primary fa fa-arrow-up me-2 d-grid"></i>80% Growth</p>
              </div>
              <div class="setting-list"></div>
            </div>
          </div>
          <div class="card-body p-0">
            <div id="chart-dashbord">
              <ClientOnly>
                <apexchart type="radialBar" height="380" :series="series" :options="chartOptions"> </apexchart>
              </ClientOnly>
            </div>
          </div>
        </div>
      </div>
      <DashboardDefaultLatestActivity />
      <DashboardDefaultRecentOrders />
    </div>
  </div>
</template>
<script lang="ts" setup>
interface LegendFormatterOpts {
  seriesIndex: number;
  w: { globals: { series: number[] } };
}
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const series = [76, 67, 61, 90];
const chartOptions = {
  chart: {
    height: 390,
    type: 'radialBar',
  },
  plotOptions: {
    radialBar: {
      offsetY: 0,
      startAngle: 0,
      endAngle: 270,
      borderradius: 20,
      hollow: {
        margin: 5,
        size: '30%',
        background: 'transparent',
        image: undefined,
      },
      dataLabels: {
        name: {
          show: false,
        },
        value: {
          show: false,
        },
      },
    },
  },
  colors: [primary.value, secondary.value, primary.value, secondary.value],
  labels: ['Total Order', 'Total product ', 'Quantity', 'Page views'],
  legend: {
    show: true,
    floating: true,
    fontSize: '14px',
    position: 'right',
    offsetX: 200,
    fontweight: 400,
    offsetY: 15,
    fontfamily: 'Roboto',
    labels: {
      useSeriesColors: true,
    },
    markers: {
      size: 0,
    },
    formatter: (seriesName: string, opts: LegendFormatterOpts): string => {
      return `${seriesName}: ${opts.w.globals.series[opts.seriesIndex]}`;
    },
    itemMargin: {
      vertical: 3,
      horizontal: 2,
    },
  },
  responsive: [
    {
      breakpoint: 480,
      options: {
        chart: {
          show: true,
          fontSize: '10px',
        },
      },
    },
    {
      breakpoint: 390,
      options: {
        chart: {
          height: 290,
        },
      },
    },
    {
      breakpoint: 390,
      options: {
        legend: {
          fontSize: '12px',
        },
      },
    },
  ],
};
</script>
