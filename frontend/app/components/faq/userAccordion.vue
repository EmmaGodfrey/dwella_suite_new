<template>
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">
        <button
          class="btn btn-link collapsed"
          data-bs-toggle="collapse"
          data-bs-target="#collapseicon18"
          :aria-expanded="isActive4 ? 'true' : 'false'"
          v-on:click="open4()"
          aria-controls="collapseicon2"
        >
          <Icon name="mdi:help-circle-outline" class="" size="20" />Meta Tags in WordPress ?
        </button>
      </h5>
    </div>
    <div :class="[isActive4 ? 'block' : 'none', 'content']" v-show="isActive4">
      <div class="card-body">
        <p>
          Manually adding meta tags in WordPress is relatively simple. For this demo, we’ll use the example from the WordPress Codex. Imagine you’re Harriet Smith, a veterinarian who blogs about their
          animal stories on WordPress.
        </p>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const isActive4 = ref<boolean>(false);

function open4() {
  isActive4.value = !isActive4.value;
}
</script>
