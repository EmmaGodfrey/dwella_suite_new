<template>
  <div class="faq-title">
    <h6>Intellectual Property</h6>
  </div>
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">
        <button class="btn btn-link collapsed" data-bs-toggle="collapse" data-bs-target="#collapseicon5" :aria-expanded="isActive ? 'true' : 'false'" v-on:click="open()">
          <Icon name="mdi:help-circle-outline" class="" size="20" /> WordPress Site Maintenance ?
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
          data-bs-target="#collapseicon7"
          :aria-expanded="isActive1 ? 'true' : 'false'"
          v-on:click="open1()"
          aria-controls="collapseicon2"
        >
          <Icon name="mdi:help-circle-outline" class="" size="20" /> WordPress in Your Language ?
        </button>
      </h5>
    </div>
    <div :class="[isActive1 ? 'block' : 'none', 'content']" v-show="isActive1">
      <div class="card-body">
        <p>As of version 4.0, you can have WordPress automatically install the language of your choice during the installation process.</p>
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">
        <button
          class="btn btn-link collapsed"
          data-bs-toggle="collapse"
          data-bs-target="#collapseicon8"
          :aria-expanded="isActive2 ? 'true' : 'false'"
          v-on:click="open2()"
          aria-controls="collapseicon2"
        >
          <Icon name="mdi:help-circle-outline" class="" size="20" />Integrating WordPress with Your Website ?
        </button>
      </h5>
    </div>
    <div :class="[isActive2 ? 'block' : 'none', 'content']" v-show="isActive2">
      <div class="card-body">
        <p>
          How you approach this process will depend on which web host you use. For example, a lot of hosting providers use cPanel, which includes an option to set up subdomains with just a few clicks.
        </p>
      </div>
    </div>
  </div>
  <FaqSellingAccording />
</template>
<script lang="ts" setup>
const isActive = ref<boolean>(false);
const isActive1 = ref<boolean>(false);
const isActive2 = ref<boolean>(false);

function open() {
  isActive.value = !isActive.value;
}
function open1() {
  isActive1.value = !isActive1.value;
}
function open2() {
  isActive2.value = !isActive2.value;
}
</script>
