<template>
  <div class="col-sm-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Both Side Scroll</h5>
      </div>
      <div class="card-body">
        <div class="scroll-bar-wrap">
          <perfect-scrollbar class="both-side-scroll scroll-demo p-0" :settings="settings3"><img :src="getImages('banner/1.jpg')" alt="girl" width="800" height="600" /></perfect-scrollbar>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';

const settings3 = ref({
  maxScrollbarLength: 60,
});
</script>
