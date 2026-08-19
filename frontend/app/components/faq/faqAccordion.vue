<template>
  <div class="col-lg-12">
    <div class="header-faq">
      <h5 class="mb-0">Quick Questions are answered</h5>
    </div>
    <div class="row default-according style-1 faq-accordion" id="accordionoc">
      <div class="col-xl-8 xl-60 col-lg-6 col-md-7 box-col-60">
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">
              <button
                class="btn btn-link collapsed"
                data-bs-toggle="collapse"
                data-bs-target="#collapseicon"
                :aria-expanded="show3 ? 'true' : 'false'"
                aria-controls="collapseicon"
                v-on:click="open3()"
              >
                <Icon name="mdi:help-circle-outline" class="" size="20" /> Integrating WordPress with Your Website?
              </button>
            </h5>
          </div>
          <div :class="[show3 ? 'block' : 'none', 'content']" v-show="show3">
            <div class="card-body">
              <p>
                How you approach this process will depend on which web host you use. For example, a lot of hosting providers use cPanel, which includes an option to set up subdomains with just a few
                clicks.
              </p>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">
              <button class="btn btn-link collapsed" data-bs-toggle="collapse" data-bs-target="#collapseicon2" :aria-expanded="show2 ? 'true' : 'false'" aria-controls="collapseicon2" @click="open2()">
                <Icon name="mdi:help-circle-outline" class="" size="20" /> WordPress Site Maintenance ?
              </button>
            </h5>
          </div>
          <div :class="[show2 ? 'block' : 'none', 'content']" v-show="show2">
            <div class="card-body">
              <p>We’ve just published a detailed on how to backup your WordPress website, however, if you’re in a hurry, here’s a quick solution.</p>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">
              <button class="btn btn-link collapsed" data-bs-toggle="collapse" data-bs-target="#collapseicon3" :aria-expanded="show ? 'true' : 'false'" aria-controls="collapseicon2" @click="open()">
                <Icon name="mdi:help-circle-outline" class="" size="20" />Meta Tags in WordPress ?
              </button>
            </h5>
          </div>
          <div :class="[show ? 'block' : 'none', 'content']" v-show="show">
            <div class="card-body">
              <p>
                Manually adding meta tags in WordPress is relatively simple. For this demo, we’ll use the example from the WordPress Codex. Imagine you’re Harriet Smith, a veterinarian who blogs about
                their animal stories on WordPress.
              </p>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">
              <button class="btn btn-link collapsed" data-bs-toggle="collapse" data-bs-target="#collapseicon4" :aria-expanded="show1 ? 'true' : 'false'" aria-controls="collapseicon2" @click="open1()">
                <Icon name="mdi:help-circle-outline" class="" size="20" /> WordPress in Your Language ?
              </button>
            </h5>
          </div>
          <div :class="[show1 ? 'block' : 'none', 'content']" v-show="show1">
            <div class="card-body">
              <p>As of version 4.0, you can have WordPress automatically install the language of your choice during the installation process.</p>
            </div>
          </div>
        </div>
        <FaqIntellectualProperty />
      </div>
      <FaqNavigationView />
    </div>
  </div>
</template>
<script lang="ts" setup>
const show = ref<boolean>(false);
const show1 = ref<boolean>(false);
const show3 = ref<boolean>(false);
const show2 = ref<boolean>(false);
function open3() {
  show3.value = !show3.value;
}
function open() {
  show.value = !show.value;
}
function open1() {
  show1.value = !show1.value;
}
function open2() {
  show2.value = !show2.value;
}
</script>
