<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Medical Icons</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-4 col-xl-3" v-for="(medica, index) in medicalIcons" :key="index" v-on:click="iconBar(medica.name)"><i :class="'fa fa-' + medica.name"></i>{{ medica.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const medicalIcons = ref([
  { name: 'ambulance' },
  { name: 'h-square' },
  { name: 'hospital-o' },
  { name: 'medkit' },
  { name: 'plus-square' },
  { name: 'stethoscope' },
  { name: 'user-md' },
  { name: 'wheelchair' },
]);
const emit = defineEmits(['selected']);

function iconBar(icon: string) {
  emit('selected', icon);
}
</script>

<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
