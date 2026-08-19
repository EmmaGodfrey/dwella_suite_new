<template>
  <ClientOnly>
    <apexchart :height="height" :type="type" :options="options" :series="series" />
  </ClientOnly>
</template>
<script lang="ts" setup>
import apexchart from 'vue3-apexcharts';

const props = defineProps<{
  height: string;
  type: string;
  options: string;
  series: string;
}>();
</script>
