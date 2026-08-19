<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Abstract</h5>
        <span>New</span>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-4 col-xl-3" v-for="(ab, index) in abstract" :key="index" v-on:click="iconBar(ab.name)"><i :class="'icofont icofont-' + ab.name"></i>{{ ab.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { abstract } from '~/composables/flagIcon';

const emit = defineEmits(['selected']);

function iconBar(icon: string) {
  emit('selected', icon);
}
</script>

<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
