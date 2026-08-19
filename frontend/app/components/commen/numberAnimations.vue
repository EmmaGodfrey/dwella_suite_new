<template>
  <ClientOnly>
    <number class="bold counter" ref="number2" :from="0" :to="data" :format="theFormat" :duration="5" :delay="0" easing="Power1.easeOut" />
  </ClientOnly>
</template>
<script lang="ts" setup>
let props = defineProps<{
  data: string;
}>();
function theFormat(number: number) {
  return number.toFixed(1);
}
</script>
