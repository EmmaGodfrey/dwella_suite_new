<template>
  <div class="col-sm-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Vertical Scroll</h5>
      </div>
      <div class="card-body">
        <perfect-scrollbar class="vertical-scroll scroll-demo" :settings="settings6">
          <p v-for="(item, index) in vertical" :key="index">{{ item.desc }}</p>
        </perfect-scrollbar>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useScrollableStore } from '~/store/scrollable';

const store = useScrollableStore();
const { vertical } = storeToRefs(store);
const settings6 = {
  maxScrollbarLength: 60,
};
</script>
