<template>
  <div class="col-xl-8 col-md- des-xl-100 box-col-12">
    <div class="row">
      <div class="col-xl-3 col-sm-6 box-col-3 chart_data_right">
        <div class="card income-card card-secondary">
          <div class="card-body align-items-center">
            <div class="round-progress knob-block text-center">
              <div class="progress-circle">
                <ClientOnly>
                  <apexchart type="radialBar" height="140" ref="chart" :options="chartOptions" :series="series"></apexchart>
                </ClientOnly>
              </div>
              <h5>$9,84,235</h5>
              <p>Our Annual Income</p>
            </div>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-sm-6 box-col-3 chart_data_right second">
        <div class="card income-card card-primary">
          <div class="card-body">
            <div class="round-progress knob-block text-center">
              <div class="progress-circle">
                <ClientOnly>
                  <apexchart type="radialBar" height="140" ref="chart" :options="chartOption" :series="series1"></apexchart>
                </ClientOnly>
              </div>
              <h5>$4,55,462</h5>
              <p>Our Annual Income</p>
            </div>
          </div>
        </div>
      </div>
      <DashboardEcommerceSellingProduct />
      <DashboardEcommerceTotalSelling />
      <DashboardEcommerceOurTarget />
    </div>
  </div>
</template>
<script lang="ts" setup>
import { storeToRefs } from 'pinia';

import { uselayoutStore } from '~/store/layout';

var { primaryColor: primaryRef, secondaryColor: secondaryRef } = storeToRefs(uselayoutStore());
var primary = primaryRef.value;
var secondary = '#ba895d';
const series = [60];
const series1 = [60];
const chartOptions = {
  chart: {
    height: 200,
    type: 'radialBar',
  },
  plotOptions: {
    radialBar: {
      hollow: {
        size: '40%',
      },
      dataLabels: {
        name: {
          fontSize: '20px',
          show: false,
          color: '#fff',
        },
        value: {
          show: true,
          color: '#333',
          offsetY: 10,
          fontSize: '18px',
        },
      },
    },
  },
  colors: [secondary],
  labels: [''],
};
const chartOption = {
  chart: {
    height: 200,
    type: 'radialBar',
  },
  plotOptions: {
    radialBar: {
      hollow: {
        size: '40%',
      },
      dataLabels: {
        name: {
          fontSize: '16px',
          show: false,
          color: '#fff',
        },
        value: {
          show: true,
          color: '#333',
          offsetY: 10,
          fontSize: '18px',
        },
      },
    },
  },
  colors: [primary],
  labels: [''],
};
</script>
