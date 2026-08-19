<template>
  <div class="tab-pane fade" :class="{ 'active show': customizer == 'settings' }" id="c-pills-home">
    <h6>Layout Type</h6>
    <ul class="main-layout layout-grid">
      <li data-attr="ltr" :class="{ active: layoutType == 'ltr' }" @click="customizeLayoutType('ltr')">
        <div class="header bg-light">
          <ul>
            <li></li>
            <li></li>
            <li></li>
          </ul>
        </div>
        <div class="body">
          <ul>
            <li class="bg-light sidebar"></li>
            <li class="bg-light body">
              <span class="badge badge-primary">LTR</span>
            </li>
          </ul>
        </div>
      </li>
      <li data-attr="rtl" :class="{ active: layoutType == 'rtl' }" @click="customizeLayoutType('rtl')">
        <div class="header bg-light">
          <ul>
            <li></li>
            <li></li>
            <li></li>
          </ul>
        </div>
        <div class="body">
          <ul>
            <li class="bg-light body">
              <span class="badge badge-primary">RTL</span>
            </li>
            <li class="bg-light sidebar"></li>
          </ul>
        </div>
      </li>
      <li v-bind:style="boxlayout ? '' : 'display: none;'" data-attr="box" :class="{ active: layoutType == 'box-layout' }" @click="customizeLayoutType('box-layout')" class="box-layout px-3">
        <div class="header bg-light">
          <ul>
            <li></li>
            <li></li>
            <li></li>
          </ul>
        </div>
        <div class="body">
          <ul>
            <li class="bg-light sidebar"></li>
            <li class="bg-light body">
              <span class="badge badge-primary">Box</span>
            </li>
          </ul>
        </div>
      </li>
    </ul>
    <h6>SIDEBAR TYPE</h6>
    <ul class="sidebar-type layout-grid">
      <li data-attr="normal-sidebar" @click="customizeSidebarSetting('horizontal-wrapper ', 'Horizontal')">
        <div class="header bg-light">
          <ul>
            <li></li>
            <li></li>
            <li></li>
          </ul>
        </div>
        <div class="body">
          <ul>
            <li class="bg-dark sidebar"></li>
            <li class="bg-light body"></li>
          </ul>
        </div>
      </li>
      <li data-attr="compact-sidebar" @click="customizeSidebarSetting('compact-wrapper', 'Defaul')">
        <div class="header bg-light">
          <ul>
            <li></li>
            <li></li>
            <li></li>
          </ul>
        </div>
        <div class="body">
          <ul>
            <li class="bg-dark sidebar"></li>
            <li class="bg-light body"></li>
          </ul>
        </div>
      </li>
    </ul>
  </div>
</template>
<script lang="ts" setup>
import { useRouter } from 'vue-router';

import { uselayoutStore } from '~/store/layout';
import { useMenuStore } from '~/store/menu';
import type { AppConfig } from '~/types/layout';

const router = useRouter();
const layoutType = ref<string>('ltr');
const store = useMenuStore();
const { activeoverlay, customizer } = storeToRefs(store);
let storeLayout = uselayoutStore();
let { layout, boxlayout } = storeToRefs(storeLayout);
let { setCustomizeSidebarType, setLayoutType } = storeLayout;

onMounted(() => {
  if (localStorage.getItem('SidebarType') === 'compact-wrapper') {
    layout.value.settings.sidebar_setting = 'compact-wrapper';
    setCustomizeSidebarType({ type: 'compact-wrapper' });
  } else {
    layout.value.settings.sidebar_setting = 'horizontal-wrapper';
    setCustomizeSidebarType({ type: 'horizontal-wrapper' });
  }
});

function customizeLayoutType(val: string) {
  layoutType.value = val;
  setLayoutType(layout as unknown as AppConfig, val);
}
function customizeSidebarSetting(val: string, layouts: string) {
  setCustomizeSidebarType({ type: layouts });
  layout.value.settings.layout = layouts;
  router.push({ query: { layout: layouts } }).catch(err => err);
  if (layouts.split(' ').includes('compact-sidebar')) {
    activeoverlay.value = true;
    document.getElementById('mainnav');
  } else {
    activeoverlay.value = false;
    document.getElementById('mainnav');
  }
  if (layouts === 'Defaul') {
    boxlayout.value = true;
  } else {
    boxlayout.value = false;
  }
}
</script>
