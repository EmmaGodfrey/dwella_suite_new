<template>
  <div class="col-sm-12 col-xl-6 box-col-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Radar Chart</h5>
      </div>
      <div class="card-body">
        <div id="radarchart">
          <ClientOnly>
            <apexchart height="350" type="radar" :options="chartOptions" :series="series"></apexchart>
          </ClientOnly>
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
    data: [20, 100, 40, 30, 50, 80, 33],
  },
];
const chartOptions = {
  chart: {
    height: 350,
    type: 'radar',
    toolbar: {
      show: false,
    },
  },
  labels: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
  plotOptions: {
    radar: {
      size: 140,
      polygons: {
        strokeColor: primary.value,
        fill: {
          colors: ['#f8f8f8', '#fff'],
        },
      },
    },
  },
  title: {
    text: 'Radar with Polygon Fill',
  },

  responsive: [
    {
      breakpoint: 481,
      options: {
        plotOptions: {
          radar: {
            size: 100,
          },
        },
      },
    },
  ],
  markers: {
    size: 4,
    colors: ['#fff'],
    strokeColor: primary.value,
    strokeWidth: 2,
  },
  tooltip: {
    y: {
      formatter: function (val: number) {
        return val;
      },
    },
  },
  yaxis: {
    tickAmount: 7,
    labels: {
      formatter: function (val: number, i: number) {
        if (i % 2 === 0) {
          return val;
        } else {
          return '';
        }
      },
    },
  },
  colors: [secondary.value],
};
</script>
