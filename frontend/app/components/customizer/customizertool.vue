<template>
  <a class="nav-link" :class="{ 'active show': customizer == 'layouts' }" id="c-pills-home-tab" @click="openCustomizerSetting('layouts')" href="javascript:void(0)">
    <div class="settings">
      <i class="icofont icofont-laptop-alt"></i>
    </div>
    <span>Check Layout</span>
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
