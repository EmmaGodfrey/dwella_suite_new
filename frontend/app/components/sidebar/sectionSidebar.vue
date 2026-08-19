<template>
  <SidebarProfileMenu />
  <nav>
    <div class="main-navbar">
      <li class="left-arrow" :class="hideLeftArrow ? 'disabled' : hideLeftArrow" @click="display2()">
        <Icon name="iconamoon:arrow-left-1-bold" class="" size="20" />
      </li>
      <div id="mainnav">
        <ul class="nav-menu custom-scrollbar" id="myDIV" :style="[layoutobject?.split(' ').includes('horizontal-wrapper') ? { 'margin-left': margin + 'px' } : { margin: '0px' }]">
          <SidebarNavMenu />
        </ul>
      </div>
      <li class="right-arrow" :class="hideRightArrow ? 'disabled' : hideRightArrow" @click="display()">
        <Icon name="iconamoon:arrow-right-1-bold" class="" size="20" />
      </li>
    </div>
  </nav>
</template>
<script lang="ts" setup>
import { useRoute } from 'vue-router';

import { layoutClasses } from '~/constants/layout';
import { uselayoutStore } from '~/store/layout';
import { useMenuStore } from '~/store/menu';

defineEmits(['clicked']);
const route = useRoute();
const layoutobj = ref<string | undefined>(undefined);
const store = useMenuStore();
const storeLayout = uselayoutStore();
const { layout } = storeToRefs(storeLayout);
const { data, hideRightArrow, hideLeftArrow, margin, menuWidth, hideLeftArrowRTL } = storeToRefs(store);
let { setActiveRoute } = store;

const isActive = ref<boolean>(false);
const layoutobject = computed({
  get() {
    return layout.value.settings.sidebar_setting;
  },
  set() {
    layoutobj.value = layout.value.settings.sidebar_setting;

    const found = layoutClasses.find(item => Object.keys(item).pop() === layout.value.settings.layout);
    if (found) {
      layoutobj.value = JSON.parse(JSON.stringify(found))[layout.value.settings.layout];
    }

    return layoutobj.value;
  },
});
onMounted(() => {
  setTimeout(() => {
    const elmnt = document.getElementById('myDIV');
    if (elmnt) {
      menuWidth.value = elmnt.offsetWidth;
    }
    menuWidth.value > window.innerWidth ? ((hideRightArrow.value = false), (hideLeftArrowRTL.value = false)) : ((hideRightArrow.value = false), (hideLeftArrowRTL.value = true));
  }, 500);
  if (margin.value == 0) {
    hideRightArrow.value = false;
  }
});
onMounted(() => {
  data.value.filter(items => {
    setActiveRoute(items);
    if (!items.children) return false;
    setActiveRoute(items);
    items.children.filter(subItems => {
      if (subItems.path == route.path) setActiveRoute(subItems);
      if (!subItems.children) return false;
      subItems.children.filter(item => {
        if (item.path == route.path) setActiveRoute(item);
      });
    });
  });
});
function display() {
  if (isActive.value == false) {
    isActive.value = !isActive.value;
  }
  if (margin.value >= -4500) {
    margin.value = margin.value - 500;
    hideLeftArrow.value = false;
    hideRightArrow.value = false;
  }
  if (margin.value == -4500) {
    hideRightArrow.value = true;
  }
}
function display2() {
  if (margin.value <= -500) {
    margin.value = margin.value + 500;
    hideLeftArrow.value = false;
    hideRightArrow.value = false;
  }
  if (margin.value == 0) {
    hideLeftArrow.value = true;
  }
}
</script>
