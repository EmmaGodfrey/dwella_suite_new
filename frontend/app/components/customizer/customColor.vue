<template>
  <div class="tab-pane fade" :class="{ 'active show': customizer == 'colors' }" id="c-pills-home">
    <h6 class="">Unlimited Color</h6>
    <ul class="layout-grid unlimited-color-layout">
      <input id="ColorPicker1" type="color" v-model="primary" name="Background" />
      <input id="ColorPicker2" type="color" v-model="secondary" name="Background" />
      <button type="button" class="color-apply-btn btn btn-primary color-apply-btn" @click="customizeColor">Apply</button>
    </ul>
    <h6 class="">Mix Layout</h6>
    <ul class="layout-grid customizer-mix">
      <li class="color-layout" data-attr="light-only" :class="{ active: mixLayout == 'light-only' }" @click="customizeMixLayout('light-only')">
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
            <li class="bg-light body"></li>
          </ul>
        </div>
      </li>
      <li class="color-layout" data-attr="dark-sidebar" :class="{ active: mixLayout == 'dark-sidebar' }" @click="customizeMixLayout('dark-sidebar')">
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
      <li class="color-layout" data-attr="dark-only" :class="{ active: mixLayout == 'dark-only' }" @click="customizeMixLayout('dark-only')">
        <div class="header bg-dark">
          <ul>
            <li></li>
            <li></li>
            <li></li>
          </ul>
        </div>
        <div class="body">
          <ul>
            <li class="bg-dark sidebar"></li>
            <li class="bg-dark body"></li>
          </ul>
        </div>
      </li>
    </ul>
  </div>
</template>
<script lang="ts" setup>
import { uselayoutStore } from '~/store/layout';
import { useMenuStore } from '~/store/menu';

const mixLayout = ref<string>('default');
let primary = ref<string>('#24695c');
let secondary = ref<string>('#ba895d');
const store = useMenuStore();
const { customizer } = storeToRefs(store);
let storeLayout = uselayoutStore();
let { setColorScheme } = storeLayout;
onMounted(() => {
  let primarycol = useCookie('primary_color').value;
  let secondarycol = useCookie('secondary_color').value;
  primary.value = primarycol ? primarycol : '#24695c';
  secondary.value = secondarycol ? secondarycol : '#ba895d';
});
function customizeMixLayout(val: string) {
  mixLayout.value = val;
  document.body.className = val;
}
function customizeColor() {
  let primarycol = useCookie('primary_color').value;
  let secondarycol = useCookie('secondary_color').value;
  setColorScheme({ primary: primary.value, secondary: secondary.value });
  primary.value = primarycol ? primarycol : '#24695c';
  secondary.value = secondarycol ? secondarycol : '#ba895d';
}
</script>
