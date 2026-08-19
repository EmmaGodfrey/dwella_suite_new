<template>
  <TheBreadcrumbs main="Icons" title="Flag Icons" />
  <div class="container-fluid">
    <div class="row">
      <div class="col-sm-12">
        <div class="card">
          <div class="card-header pb-0">
            <h5 class="m-b-0">Flag Icons</h5>
          </div>
          <div class="card-body">
            <div class="row icon-lists flag-icons">
              <div class="col-12 col-sm-6 col-xl-4" v-for="(fi, index) in flagIcons" :key="index" v-on:click="iconBar(fi.abbrivation)">
                <div class="media">
                  <i class="flag-icon" :class="'flag-icon-' + fi.abbrivation"></i>
                  <div class="media-body align-self-center">
                    <h5 v-text="fi.abbrivation"></h5>
                    <h6 class="mt-0" v-text="fi.name"></h6>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="icon-hover-bottom p-fixed fa-fa-icon-show-div" :class="{ 'opecity-0': !iconBarStatus }" :style="[iconBarStatus ? { display: 'block' } : { display: 'none' }]">
    <div class="container-fluid">
      <div class="row">
        <div class="icon-popup">
          <div class="close-icon" v-on:click="closeIconBar">
            <i class="icofont icofont-close"></i>
          </div>
          <div class="icon-first">
            <i class="fa-2x" :class="[selectIcon.class]"></i>
          </div>
          <div class="icon-class">
            <label class="icon-title">Class</label>
            <span>icon-drupal</span>
          </div>
          <div class="icon-last icon-last">
            <label class="icon-title">Markup</label>
            <div class="form-inline">
              <div class="form-group">
                <input class="inp-val form-control m-r-10" type="text" :value="selectIcon.tag" />
                <button class="btn btn-primary notification mt-2" @click="copyIcon">Copy text</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { toast } from 'vue3-toastify';

import { iconBarStatus, selectIcon, flagIcons } from '~/composables/flagIcon';

import 'vue3-toastify/dist/index.css';

useHead({
  title: 'Icons Flag | Cion - Premium Nuxt Admin Template',
});

function iconBar(icon: string) {
  selectIcon.value.class = 'flag-icon flag-icon-' + icon;
  selectIcon.value.tag = '<i class="flag-icon flag-icon-' + icon + '"></i>';

  iconBarStatus.value = true;
}
function closeIconBar() {
  iconBarStatus.value = false;
}
function copyIcon() {
  toast.success(' Code Copied to clipboard! ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'bottom-right',
  });
  navigator.clipboard.writeText(selectIcon.value.tag);
  document.execCommand('copy');
}
</script>
