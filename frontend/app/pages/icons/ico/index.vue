<template>
  <TheBreadcrumbs main="Icons" title="ICO Icon" />
  <div class="container-fluid">
    <div class="row">
      <IconsIcoIconAbstractIcon @selected="iconBar" />
      <IconsIcoIconAnimalIcon @selected="iconBar" />
      <IconsIcoIconBrandIcons @selected="iconBar" />
      <IconsIcoIconBusinessIcons @selected="iconBar" />
      <IconsIcoIconChartIcons @selected="iconBar" />
      <IconsIcoIconConstructionIcons @selected="iconBar" />
      <IconsIcoIconCurrencyIcons @selected="iconBar" />
      <IconsIcoIconDeviceIcons @selected="iconBar" />
      <IconsIcoIconDirectionalIcons @selected="iconBar" />
      <IconsIcoIconEducationIcons @selected="iconBar" />
      <IconsIcoIconEmoticonIcons @selected="iconBar" />
      <IconsIcoIconFiletypeIcons @selected="iconBar" />
      <IconsIcoIconFoodIcons @selected="iconBar" />
      <IconsIcoIconKidsIcons @selected="iconBar" />
      <IconsIcoIconLawIcons @selected="iconBar" />
      <IconsIcoIconMathematicalIcons @selected="iconBar" />
      <IconsIcoIconMedicalIcons @selected="iconBar" />
      <IconsIcoIconMobileIcons @selected="iconBar" />
      <IconsIcoIconMultimediaIcons @selected="iconBar" />
      <IconsIcoIconPaymentIcons @selected="iconBar" />
      <IconsIcoIconPersonIcons @selected="iconBar" />
      <IconsIcoIconSearchIcons @selected="iconBar" />
      <IconsIcoIconSocialIcons @selected="iconBar" />
      <IconsIcoIconSportIcons @selected="iconBar" />
      <IconsIcoIconTextIcons @selected="iconBar" />
      <IconsIcoIconTransportIcons @selected="iconBar" />
      <IconsIcoIconTravelIcons @selected="iconBar" />
      <IconsIcoIconWeatherIcons @selected="iconBar" />
      <IconsIcoIconWebIcons @selected="iconBar" />
    </div>
  </div>
  <div class="icon-hover-bottom p-fixed fa-fa-icon-show-div" :class="{ 'opecity-0': !iconBarStatus }" :style="[iconBarStatus ? { display: 'block' } : { display: 'none' }]">
    <div class="container-fluid">
      <div class="row">
        <div class="icon-popup">
          <div class="close-icon" v-on:click="closeIconBar"><i class="icofont icofont-close"></i></div>
          <div class="icon-first"><i class="fa-2x" :class="[selectIcon.class]"></i></div>
          <div class="icon-class"><label class="icon-title">Class</label><span>icon-drupal</span></div>
          <div class="icon-last icon-last">
            <label class="icon-title">Markup</label>
            <div class="form-inline">
              <div class="form-group">
                <input class="inp-val form-control m-r-10" type="text" :value="selectIcon.tag" />
                <button class="btn btn-primary notification mt-2" v-on:click="copyIcon">Copy text</button>
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

import { iconBarStatus, selectIcon } from '~/composables/flagIcon';

import 'vue3-toastify/dist/index.css';

useHead({
  title: 'Icons Icon | Cion - Premium Nuxt Admin Template',
});

function iconBar(icon: string) {
  selectIcon.value.class = 'icofont icofont-' + icon;
  selectIcon.value.tag = '<i class="icofont icofont-' + icon + '"></i>';
  iconBarStatus.value = true;
}
function closeIconBar() {
  iconBarStatus.value = false;
}
function copyIcon() {
  toast.success('Code Copied to clipboard! ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'bottom-right',
  });
  navigator.clipboard.writeText(selectIcon.value.tag);
  document.execCommand('copy');
}
</script>
