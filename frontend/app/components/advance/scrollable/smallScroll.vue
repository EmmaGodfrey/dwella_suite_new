<template>
  <div class="col-sm-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Small Size Scroll</h5>
      </div>
      <div class="card-body">
        <div class="scroll-bar-wrap">
          <perfect-scrollbar class="scrollbar-margins large-margin scroll-demo p-0" :settings="settings"
            ><img :src="getImages('banner/3.jpg')" alt="girl" width="800" height="600"
          /></perfect-scrollbar>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';

const settings = ref({
  maxScrollbarLength: 60,
});
</script>
