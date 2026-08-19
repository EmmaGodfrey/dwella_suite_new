<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Arrows & Direction Icons</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-6 col-lg-4" v-for="(di, index) in directional" :key="index" v-on:click="iconBar(di.name)"><i :class="di.name"></i>{{ di.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const directional = ref([
  { name: 'icon-arrow-up' },
  { name: 'icon-arrow-right' },
  { name: 'icon-arrow-left' },
  { name: 'icon-arrow-down' },
  { name: 'icon-arrows-vertical' },
  { name: 'icon-arrows-horizontal' },
  { name: 'icon-angle-up' },
  { name: 'icon-angle-right' },
  { name: 'icon-angle-left' },
  { name: 'icon-angle-down' },
  { name: 'icon-angle-double-up' },
  { name: 'icon-angle-double-right' },
  { name: 'icon-angle-double-left' },
  { name: 'icon-angle-double-down' },
  { name: 'icon-move' },
  { name: 'icon-fullscreen' },
  { name: 'icon-arrow-top-right' },
  { name: 'icon-arrow-top-left' },
  { name: 'icon-arrow-circle-up' },
  { name: 'icon-arrow-circle-right' },
  { name: 'icon-arrow-circle-left' },
  { name: 'icon-arrow-circle-down' },
  { name: 'icon-arrows-corner' },
  { name: 'icon-split-v' },
  { name: 'icon-split-v-alt' },
  { name: 'icon-split-h' },
  { name: 'icon-hand-point-up' },
  { name: 'icon-hand-point-right' },
  { name: 'icon-hand-point-left' },
  { name: 'icon-hand-point-down' },
  { name: 'icon-back-right' },
  { name: 'icon-back-left' },
  { name: 'icon-exchange-vertical' },
]);
const emit = defineEmits(['selected']);
function iconBar(icon: string) {
  emit('selected', icon);
}
</script>
<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
