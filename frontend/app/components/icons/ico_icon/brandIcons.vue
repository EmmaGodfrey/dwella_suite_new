<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Brand</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-4 col-xl-3" v-for="(br, index) in brand" :key="index" v-on:click="iconBar(br.name)"><i :class="'icofont icofont-' + br.name"></i>{{ br.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { brand } from '~/composables/flagIcon';

const emit = defineEmits(['selected']);

function iconBar(icon: string) {
  emit('selected', icon);
}
</script>
<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
