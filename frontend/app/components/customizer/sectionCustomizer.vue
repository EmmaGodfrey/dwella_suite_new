<template>
  <div class="customizer-links" :class="{ open: customizer }">
    <div class="nav flex-column nac-pills" id="c-pills-tab" role="tablist" aria-orientation="vertical">
      <CustomizerCustomizertool />
      <CustomizerCustomizersetting />
      <CustomizerCustomizercolor />
    </div>
    <div class="customizer-contain" :class="{ open: customizer }">
      <div class="tab-content" id="c-pills-tabContent">
        <CustomizerConfigurationView />
        <div class="customizer-body custom-scrollbar">
          <CustomizerCustomlayout />
          <CustomizerCustomSetting />
          <CustomizerCustomColor />
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useMenuStore } from '~/store/menu';

const store = useMenuStore();
const { customizer } = storeToRefs(store);
</script>
