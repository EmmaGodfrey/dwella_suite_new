<template>
  <div class="col-sm-6 col-xl-3 xl-25 col-lg-6 box-col-6" v-for="(item, index) in data" :key="index">
    <div class="card social-widget-card">
      <div class="card-body">
        <div class="redial-social-widget radial-bar-70" data-label="50%">
          <i class="font-primary fa" :class="item.icon"></i>
        </div>
        <h5 class="b-b-light">{{ item.title }}</h5>
        <div class="row">
          <div class="col text-center b-r-light">
            <span>Post</span>
            <h4 class="counter mb-0">
              <CommenNumberAnimations class="bold counter" :data="item.post" />
            </h4>
          </div>
          <div class="col text-center">
            <span>Like</span>
            <h4 class="counter mb-0">
              <CommenNumberAnimations :data="item.like" />
            </h4>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useWidgetsStore } from '~/store/widgets';

const store = useWidgetsStore();
const { social } = storeToRefs(store);
const data = social.value;
</script>
