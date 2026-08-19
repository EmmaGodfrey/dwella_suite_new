<template>
  <a class="nav-link" :class="{ 'active show': customizer == 'colors' }" id="c-pills-home-tab" @click="openCustomizerSetting('colors')" href="javascript:void(0)">
    <div class="settings">
      <i class="icofont icofont-color-bucket"></i>
    </div>
    <span>Color Picker</span>
  </a>
</template>

<script lang="ts" setup>
import { useMenuStore } from '~/store/menu';

const store = useMenuStore();
const { customizer } = storeToRefs(store);
function openCustomizerSetting(val: string) {
  customizer.value = val;
}
</script>
