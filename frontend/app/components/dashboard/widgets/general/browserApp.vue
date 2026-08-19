<template>
  <div class="col-xl-4 col-sm-6 col-sm-12" v-for="(item, index) in data" :key="index">
    <div class="card browser-widget">
      <div class="media card-body">
        <div class="media-img"><img :src="item.img" alt="" /></div>
        <div class="media-body align-self-center">
          <div>
            <p>Daily</p>
            <h4>
              <span class="counter"> <CommenNumberAnimations :data="item.daily" /> </span>%
            </h4>
          </div>
          <div>
            <p>Month</p>
            <h4>
              <span class="counter"> <CommenNumberAnimations :data="item.month" /> </span>%
            </h4>
          </div>
          <div>
            <p>Week</p>
            <h4>
              <span class="counter"> <CommenNumberAnimations :data="item.week" /> </span>%
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
const { brow } = storeToRefs(store);
const data = brow.value;
</script>
