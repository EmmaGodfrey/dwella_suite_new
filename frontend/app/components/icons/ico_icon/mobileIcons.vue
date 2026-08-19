<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Mobile UI</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-6 col-lg-4" v-for="(mobi, index) in mobileui" :key="index" v-on:click="icon_bar(mobi.name)"><i :class="'icofont icofont-' + mobi.name"></i>{{ mobi.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { mobileui } from '~/composables/flagIcon';

const emit = defineEmits(['selected']);

function icon_bar(icon: string) {
  emit('selected', icon);
}
</script>
<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
