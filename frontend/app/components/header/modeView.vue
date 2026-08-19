<template>
  <div class="mode" :class="actives ? 'active' : ''">
    <i class="fa fa-moon-o" v-show="mixLayout == 'light-only'" @click="customizeMixLayout('dark-only')"></i>
    <i class="fa fa-lightbulb-o" v-show="mixLayout == 'dark-only'" @click="customizeMixLayout('light-only')"></i>
  </div>
</template>
<script lang="ts" setup>
import { uselayoutStore } from '~/store/layout';

const mixLayout = ref<string>('light-only');
const actives = ref<boolean>(false);
let store = uselayoutStore();
let { setLayout } = store;
onMounted(() => {
  const savedMode = localStorage.getItem('mode');
  if (savedMode) {
    mixLayout.value = savedMode;
    actives.value = savedMode === 'dark-only';
    setLayout({ class: savedMode });
  }
});

watch(mixLayout, newValue => {
  localStorage.setItem('mode', newValue);
});
function customizeMixLayout(val: string) {
  mixLayout.value = val;
  actives.value = !actives.value;
  setLayout({ class: val });
}
</script>
