<template>
  <div class="loader-wrapper" v-if="showLoader">
    <div class="theme-loader">
      <div class="loader-p"></div>
    </div>
  </div>
  <slot v-else />
</template>
<script setup lang="ts">
import { useRouter } from 'vue-router';

const showLoader = ref<boolean>(false);
const router = useRouter();

watch(
  () => router,
  () => {
    showLoader.value = true;
    setTimeout(() => {
      showLoader.value = false;
    }, 2000);
  },
  { deep: true },
);
</script>
