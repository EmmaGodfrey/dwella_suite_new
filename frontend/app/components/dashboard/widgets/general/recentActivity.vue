<template>
  <div class="col-xl-4 col-md-6 box-col-4">
    <div>
      <div class="card card-activity">
        <div class="card-header pb-0 d-flex justify-content-between align-items-center">
          <h5 class="text-uppercase">Recent Activity</h5>
        </div>
        <div class="card-body">
          <ul class="crm-activity">
            <li class="media" v-for="(item, index) in data" :key="index">
              <span class="me-3" :class="item.class">{{ item.alfabet }}</span>
              <div class="align-self-center media-body">
                <h6 class="mt-0">{{ item.title }}</h6>
                <ul class="dates">
                  <li>{{ item.date }}</li>
                  <li>{{ item.time }}</li>
                </ul>
              </div>
            </li>
            <li class="media">
              <div class="align-self-center media-body">
                <ul class="dates">
                  <li>25 July 2017</li>
                  <li>20 hours ago</li>
                </ul>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useWidgetsStore } from '~/store/widgets';

const store = useWidgetsStore();
const { recent } = storeToRefs(store);
const data = recent.value;
</script>
