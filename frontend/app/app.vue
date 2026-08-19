<template>
  <div class="loader-wrapper" v-if="showLoader">
    <div class="theme-loader">
      <div class="loader-p"></div>
    </div>
  </div>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>
<script setup lang="ts">
import { useRouter } from 'vue-router';

import { useProductsStore } from '~/store/products';

const showLoader = ref<boolean>(true);
const router = useRouter();
function add() {
  let localItem = JSON.stringify(useProductsStore().cart);
  localStorage.setItem('cart', localItem);
}
onMounted(() => {
  showLoader.value = true;
  setTimeout(() => {
    showLoader.value = false;
  }, 3000);
});

onMounted(() => {
  let allBgImageCover = document.getElementsByClassName('bg-img-cover');
  window.addEventListener('beforeunload', add);
  useProductsStore().intialUpload(JSON.parse(localStorage.getItem('cart')) || []);
});
onUnmounted(() => {
  window.removeEventListener('beforeunload', add);
});
</script>
<style lang="scss"></style>
