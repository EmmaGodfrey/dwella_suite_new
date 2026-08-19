<template>
  <div class="faq-title">
    <h6>Selling And Buying</h6>
  </div>
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">
        <button class="btn btn-link collapsed" data-bs-toggle="collapse" data-bs-target="#collapseicon9" :aria-expanded="isActive ? 'true' : 'false'" v-on:click="open()">
          <Icon name="mdi:help-circle-outline" class="" size="20" />
          WordPress Site Maintenance ?
        </button>
      </h5>
    </div>
    <div :class="[isActive ? 'block' : 'none', 'content']" v-show="isActive">
      <div class="card-body">
        <p>We’ve just published a detailed on how to backup your WordPress website, however, if you’re in a hurry, here’s a quick solution.</p>
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">
        <button
          class="btn btn-link collapsed"
          data-bs-toggle="collapse"
          data-bs-target="#collapseicon10"
          :aria-expanded="isActive1 ? 'true' : 'false'"
          v-on:click="open1()"
          aria-controls="collapseicon2"
        >
          <Icon name="mdi:help-circle-outline" class="" size="20" />Meta Tags in WordPress ?
        </button>
      </h5>
    </div>
    <div :class="[isActive1 ? 'block' : 'none', 'content']" v-show="isActive1">
      <div class="card-body">
        <p>
          Manually adding meta tags in WordPress is relatively simple. For this demo, we’ll use the example from the WordPress Codex. Imagine you’re Harriet Smith, a veterinarian who blogs about their
          animal stories on WordPress.
        </p>
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">
        <button
          class="btn btn-link collapsed"
          data-bs-toggle="collapse"
          data-bs-target="#collapseicon11"
          :aria-expanded="isActive2 ? 'true' : 'false'"
          v-on:click="open2()"
          aria-controls="collapseicon2"
        >
          <Icon name="mdi:help-circle-outline" class="" size="20" />Validating a Website ?
        </button>
      </h5>
    </div>
    <div :class="[isActive2 ? 'block' : 'none', 'content']" v-show="isActive2">
      <div class="card-body">
        <p>Validating a website is the process of ensuring that the pages on the website conform to the norms or standards defined by various organizations.</p>
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">
        <button
          class="btn btn-link collapsed"
          data-bs-toggle="collapse"
          data-bs-target="#collapseicon12"
          :aria-expanded="isActive3 ? 'true' : 'false'"
          v-on:click="open3()"
          aria-controls="collapseicon2"
        >
          <Icon name="mdi:help-circle-outline" class="" size="20" />Know Your Sources ?
        </button>
      </h5>
    </div>
    <div :class="[isActive3 ? 'block' : 'none', 'content']" v-show="isActive3">
      <div class="card-body">
        <p>
          A book or set of books giving information on many subjects or on many aspects of one subject. Some are intended as an entry point into research for a general audience, some provide detailed
          information.
        </p>
      </div>
    </div>
  </div>
  <FaqUserAccounts />
</template>
<script lang="ts" setup>
const isActive = ref<boolean>(false);
const isActive1 = ref<boolean>(false);
const isActive2 = ref<boolean>(false);
const isActive3 = ref<boolean>(false);

function open() {
  isActive.value = !isActive.value;
}
function open1() {
  isActive1.value = !isActive1.value;
}
function open2() {
  isActive2.value = !isActive2.value;
}
function open3() {
  isActive3.value = !isActive3.value;
}
</script>
