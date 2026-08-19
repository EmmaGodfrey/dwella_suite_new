<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Spinner Icons</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-4 col-xl-3" v-for="(spi, index) in spinner" :key="index" v-on:click="iconBar(spi.name)"><i :class="'fa fa-' + spi.name"></i>{{ spi.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const spinner = ref([{ name: 'circle-o-notch fa-spin' }, { name: 'cog fa-spin' }, { name: 'gear fa-spin' }, { name: 'refresh fa-spin' }, { name: 'spinner fa-spin' }]);
const emit = defineEmits(['selected']);

function iconBar(icon: string) {
  emit('selected', icon);
}
</script>
