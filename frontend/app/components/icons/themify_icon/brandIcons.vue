<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Brand Icons</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-6 col-lg-4" v-for="(br, index) in brand" :key="index" v-on:click="iconBar(br.name)"><i :class="br.name"></i>{{ br.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const brand = ref([
  { name: 'icon-flickr' },
  { name: 'icon-flickr-alt' },
  { name: 'icon-instagram' },
  { name: 'icon-google' },
  { name: 'icon-github' },
  { name: 'icon-facebook' },
  { name: 'icon-dropbox' },
  { name: 'icon-dropbox-alt' },
  { name: 'icon-dribbble' },
  { name: 'icon-apple' },
  { name: 'icon-android' },
  { name: 'icon-yahoo' },
  { name: 'icon-trello' },
  { name: 'icon-stack-overflow' },
  { name: 'icon-soundcloud' },
  { name: 'icon-sharethis' },
  { name: 'icon-sharethis-alt' },
  { name: 'icon-reddit' },
  { name: 'icon-microsoft' },
  { name: 'icon-microsoft-alt' },
  { name: 'icon-linux' },
  { name: 'icon-jsfiddle' },
  { name: 'icon-joomla' },
  { name: 'icon-html5' },
  { name: 'icon-css3' },
  { name: 'icon-drupal' },
  { name: 'icon-wordpress' },
  { name: 'icon-tumblr' },
  { name: 'icon-tumblr-alt' },
  { name: 'icon-skype' },
  { name: 'icon-youtube' },
  { name: 'icon-vimeo' },
  { name: 'icon-vimeo-alt' },
  { name: 'icon-twitter' },
  { name: 'icon-twitter-alt' },
  { name: 'icon-linkedin' },
  { name: 'icon-pinterest' },
  { name: 'icon-pinterest-alt' },
  { name: 'icon-themify-logo' },
  { name: 'icon-themify-favicon' },
  { name: 'icon-themify-favicon-alt' },
]);
const emit = defineEmits(['selected']);
function iconBar(icon: string) {
  emit('selected', icon);
}
</script>
<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
