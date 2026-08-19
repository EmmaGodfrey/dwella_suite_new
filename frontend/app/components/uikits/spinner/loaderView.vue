<template>
  <div class="col-sm-6 col-md-3" v-for="(item, index) in data" :key="index">
    <h6 class="sub-title mb-0 text-center">{{ item.title }}</h6>
    <div class="loader-box">
      <div :class="item.class"></div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useUikitStore } from '~/store/uikit';

const store = useUikitStore();
const { spinner } = storeToRefs(store);
const data = spinner.value;
</script>
