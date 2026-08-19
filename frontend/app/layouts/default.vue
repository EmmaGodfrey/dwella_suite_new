<template>
  <div class="loader-wrapper" v-if="showLoader">
    <div class="theme-loader">
      <div class="loader-p"></div>
    </div>
  </div>
  <div v-else class="page-wrapper" :class="display ? 'compact-wrapper' : layoutobj">
    <div class="page-main-header" :class="{ close_icon: !togglesidebar }">
      <HeaderSectionHeader @clicked="sidebarToggle" />
    </div>
    <div class="page-body-wrapper horizontal-menu">
      <div class="bg-overlay"></div>
      <header class="main-nav" :class="!togglesidebar ? 'close_icon' : ''">
        <SidebarSectionSidebar @clicked="sidebarToggle" />
      </header>
      <div class="page-body">
        <slot></slot>
      </div>
      <FooterView />
    </div>
    <CustomizerSectionCustomizer />
  </div>
</template>
<script lang="ts" setup>
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';

import { layoutClasses } from '~/constants/layout';
import { uselayoutStore } from '~/store/layout';
import { useMenuStore } from '~/store/menu';

const sidebarToggleVar = ref<boolean>(false);
const layoutobj = ref<Record<string, string> | undefined>(undefined);
const showLoader = ref<boolean>(false);
const display = ref<boolean>(false);
let store = useMenuStore();
let { togglesidebar } = storeToRefs(store);
const router = useRouter();
const route = useRoute();
const storeLayout = uselayoutStore();
const { layout: layout } = storeToRefs(storeLayout);
watch(
  () => router.currentRoute.value.fullPath,
  () => {
    showLoader.value = true;
    setTimeout(() => (showLoader.value = false), 2000);

    const foundLayout = layoutClasses.find(item => Object.keys(item).pop() === layout.value.settings.layout);

    if (foundLayout) {
      layoutobj.value = JSON.parse(JSON.stringify(foundLayout))[layout.value.settings.layout];

      // handle small screens
      if (window.innerWidth < 991 && ['LosAngeles', 'Singapore', 'Barcelona'].includes(layout.value.settings.layout)) {
        const newlayout = JSON.parse(JSON.stringify(layoutobj.value).replace('horizontal-wrapper', 'compact-wrapper'));
        layoutobj.value = JSON.parse(JSON.stringify(newlayout));
      }
    }
  },
  { deep: true },
);

watch(
  () => router,
  () => {
    showLoader.value = true;
    setTimeout(() => {
      showLoader.value = false;
    }, 2000);
  },
  { deep: true },
);
function sidebarToggle(value: boolean) {
  sidebarToggleVar.value = !value;
}

function handleScroll() {
  if (window.innerWidth <= 1199) {
    display.value = true;
  } else {
    display.value = false;
  }
}

onMounted(() => {
  const layoutQuery = route.query.layout;
  layout.value.settings.layout = Array.isArray(layoutQuery) ? (layoutQuery[0] ?? 'Defaul') : (layoutQuery as string) || 'Defaul';

  window.addEventListener('resize', handleScroll);

  const foundLayout = layoutClasses.find(item => Object.keys(item).pop() === layout.value.settings.layout);

  if (foundLayout) {
    layoutobj.value = JSON.parse(JSON.stringify(foundLayout))[layout.value.settings.layout];
  }

  store.initializeSidebar();
  store.initializeActiveMenu(route.path);
});
</script>
