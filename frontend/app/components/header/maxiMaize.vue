<template>
  <a class="text-dark" href="javascript:void(0)" @click.prevent="toggleFullscreen">
    <Icon name="humbleicons:maximize" class="" size="20" />
  </a>
</template>
<script lang="ts" setup>
let fullScreen = ref<boolean>(false);

function toggleFullscreen() {
  if (fullScreen.value) {
    fullScreen.value = false;
    document.exitFullscreen();
  } else {
    document.documentElement.requestFullscreen();
    fullScreen.value = true;
  }
}
</script>
