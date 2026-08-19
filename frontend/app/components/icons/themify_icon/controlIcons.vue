<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Control Icons</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-6 col-lg-4" v-for="(con, index) in control" :key="index" v-on:click="iconBar(con.name)"><i :class="con.name"></i>{{ con.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const customAnimation = {
  enter: 'animated bounce',
  exit: 'animated bounce',
};
const emit = defineEmits(['selected']);

const control = ref([
  { name: 'icon-control-stop' },
  { name: 'icon-control-shuffle' },
  { name: 'icon-control-play' },
  { name: 'icon-control-pause' },
  { name: 'icon-control-forward' },
  { name: 'icon-control-backward' },
  { name: 'icon-volume' },
  { name: 'icon-control-skip-forward' },
  { name: 'icon-control-skip-backward' },
  { name: 'icon-control-record' },
  { name: 'icon-control-eject' },
]);
function iconBar(icon: string) {
  emit('selected', icon);
}
</script>
<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
