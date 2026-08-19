<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Form Control Icons</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-4 col-xl-3" v-for="(form, index) in formIcons" :key="index" v-on:click="iconBar(form.name)"><i :class="'fa fa-' + form.name"></i>{{ form.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const formIcons = ref([
  { name: 'check-square' },
  { name: 'check-square-o' },
  { name: 'circle' },
  { name: 'circle-o' },
  { name: 'dot-circle-o' },
  { name: 'minus-square' },
  { name: 'minus-square-o' },
  { name: 'plus-square' },
  { name: 'plus-square-o' },
  { name: 'square' },
  { name: 'square-o' },
]);
const emit = defineEmits(['selected']);

function iconBar(icon: string) {
  emit('selected', icon);
}
</script>

<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
