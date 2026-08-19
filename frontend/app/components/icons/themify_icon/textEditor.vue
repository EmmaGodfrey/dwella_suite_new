<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Text Editor</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-6 col-lg-4" v-for="(texte, index) in texteditor" :key="index" v-on:click="iconBar(texte.name)"><i :class="texte.name"></i>{{ texte.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const texteditor = ref([
  { name: 'icon-paragraph' },
  { name: 'icon-uppercase' },
  { name: 'icon-underline' },
  { name: 'icon-text' },
  { name: 'icon-Italic' },
  { name: 'icon-smallcap' },
  { name: 'icon-list' },
  { name: 'icon-list-ol' },
  { name: 'icon-align-right' },
  { name: 'icon-align-left' },
  { name: 'icon-align-justify' },
  { name: 'icon-align-center' },
  { name: 'icon-quote-right' },
  { name: 'icon-quote-left' },
]);
const emit = defineEmits(['selected']);
function iconBar(icon: string) {
  emit('selected', icon);
}
</script>
<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
