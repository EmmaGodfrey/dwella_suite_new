<template>
  <div class="logo-wrapper">
    <nuxt-link to="/">
      <img class="img-fluid for-light" src="/images/logo/logo.png" alt="" />
    </nuxt-link>
  </div>
  <div class="dark-logo-wrapper">
    <nuxt-link to="/"><img class="img-fluid" src="/images/logo/dark-logo.png" alt="" /></nuxt-link>
  </div>
  <div class="toggle-sidebar" @click="toggleSidebar()">
    <Icon name="uim:align-center" class="status_toggle middle" size="20" />
  </div>
</template>
<script lang="ts" setup>
import { useMenuStore } from '~/store/menu';

let store = useMenuStore();
let { toggleSidebar } = store;
</script>
