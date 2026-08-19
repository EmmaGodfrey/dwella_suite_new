<template>
  <div class="tab-pane fade" :class="{ 'active show': customizer == 'layouts' }" id="c-pills-home">
    <ul class="sidebar-type layout-grid layout-types">
      <li data-attr="compact-sidebar">
        <div class="layout-img">
          <a @click="handlePageLayputs('compact-wrapper', 'Defaul')"><img src="/images/demo/1.jpg" class="img-fluid" alt="oneone" /></a>

          <h6>Defaul layout</h6>
        </div>
      </li>
      <li class="only-body" data-attr="default-body">
        <div class="layout-img">
          <a @click="handlePageLayputs('compact-wrapper compact-sidebar', 'Compact')"><img src="/images/demo/2.jpg" class="img-fluid" alt="one" /></a>

          <h6>Compact layout</h6>
        </div>
      </li>
      <li data-attr="modern-layout">
        <div class="layout-img">
          <a @click="handlePageLayputs('compact-wrapper modern-sidebar ', 'Modern')"> <img src="/images/demo/3.jpg" class="img-fluid" alt="one" /></a>
          <h6>Modern layout</h6>
        </div>
      </li>
    </ul>
  </div>
</template>
<script lang="ts" setup>
import { useRouter } from 'vue-router';

import { uselayoutStore } from '~/store/layout';
import { useMenuStore } from '~/store/menu';

const router = useRouter();

const store = useMenuStore();
let storeLayout = uselayoutStore();
let { activeoverlay, customizer } = storeToRefs(store);
let { layout, boxlayout } = storeToRefs(storeLayout);
let { setCustomizeSidebarType } = storeLayout;

function handlePageLayputs(val: string, layouts: string) {
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
