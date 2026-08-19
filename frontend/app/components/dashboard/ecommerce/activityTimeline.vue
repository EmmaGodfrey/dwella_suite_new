<template>
  <div class="col-xl-4 des-xl-50 box-col-12 activity-sec chart_data_left">
    <div class="card">
      <div class="card-header">
        <div class="header-top d-sm-flex justify-content-between align-items-center">
          <h5 class="m-0">Activity Timeline</h5>
          <div class="center-content">
            <p>Yearly User 24.65k</p>
          </div>
        </div>
      </div>
      <div class="card-body">
        <div class="chart-main activity-timeline update-line">
          <div class="media">
            <div class="activity-line"></div>
            <div class="activity-dot-primary"></div>
            <div class="media-body d-block">
              <h6><span class="font-primary">20-04-2021</span>Today</h6>
              <h5>Updated Product<i class="fa fa-circle circle-dot-primary pull-right"></i></h5>
              <p>Quisque a consequat ante Sit amet magna at volutapt.</p>
            </div>
          </div>
          <div class="media" v-for="(item, index) in data" :key="index">
            <div class="activity-dot-primary"></div>
            <div class="media-body d-block">
              <h6>
                <span class="font-primary">{{ item.date }}</span
                >Today<span class="badge pill-badge-primary m-l-10" v-if="item.pin">{{ item.pill }}</span>
              </h6>
              <h5>{{ item.title }} <i class="fa fa-circle circle-dot-primary pull-right"></i></h5>
              <p>{{ item.desc }}</p>
              <ul class="timeline-pro">
                <li v-for="(items, index) in item.img" :key="index"><img class="img-fluid" :src="items.img" alt="Product-1" /></li>
              </ul>
            </div>
          </div>
          <div class="media">
            <div class="media-body d-block">
              <div class="tomorrow-sec">
                <p>Tomorrow</p>
              </div>
            </div>
          </div>
          <div class="media">
            <div class="activity-dot-primary"></div>
            <div class="media-body d-block">
              <h6><span class="font-primary">20-04-20121</span>Tomorrow</h6>
              <h5>Today Total Revenue<i class="fa fa-circle circle-dot-primary pull-right"></i></h5>
              <p>Quisque a consequat ante Sit amet magna at volutapt.</p>
            </div>
          </div>
          <div class="media">
            <div class="activity-dot-primary"></div>
            <div class="media-body d-block">
              <div class="hospital-small-chart">
                <div id="column-chart">
                  <ChartActivityChart />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useDashboardStore } from '~/store/dashboard';

const store = useDashboardStore();
const { activity } = storeToRefs(store);
const data = activity.value;
</script>
