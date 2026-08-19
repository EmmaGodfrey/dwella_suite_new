<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Video Player Icons</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-4 col-xl-3" v-for="(video, index) in videoIcons" :key="index" v-on:click="iconBar(video.name)"><i :class="'fa fa-' + video.name"></i>{{ video.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const videoIcons = ref([
  { name: 'arrows-alt' },
  { name: 'backward' },
  { name: 'compress' },
  { name: 'eject' },
  { name: 'expand' },
  { name: 'fast-backward' },
  { name: 'fast-forward' },
  { name: 'forward' },
  { name: 'pause' },
  { name: 'play' },
  { name: 'play-circle' },
  { name: 'play-circle-o' },
  { name: 'step-backward' },
  { name: 'step-forward' },
  { name: 'stop' },
  { name: 'youtube-play' },
]);
const emit = defineEmits(['selected']);

function iconBar(icon: string) {
  emit('selected', icon);
}
</script>

<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
