<template>
  <a class="nav-link" :class="{ 'active show': customizer == 'settings' }" id="c-pills-home-tab" @click="openCustomizerSetting('settings')" href="javascript:void(0)">
    <div class="settings">
      <i class="icofont icofont-ui-settings"></i>
    </div>
    <span>Sidebar Type</span>
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
