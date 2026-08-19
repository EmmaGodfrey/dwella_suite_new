<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>How to use it?</h5>
        <span>All you have to do is to add animation name class attribute to html element, like :<code>Fade</code></span>
      </div>
      <div class="card-body options">
        <div v-for="(item, index) in option" :key="index">{{ item }}</div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { option } from '~/composables/commen/animationView';
</script>
