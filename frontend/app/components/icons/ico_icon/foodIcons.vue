<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Food</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-6 col-lg-4" v-for="(foo, index) in food" :key="index" v-on:click="iconBar(foo.name)"><i :class="'icofont icofont-' + foo.name"></i>{{ foo.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { food } from '~/composables/flagIcon';

const emit = defineEmits(['selected']);

function iconBar(icon: string) {
  emit('selected', icon);
}
</script>
<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
