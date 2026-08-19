import apexchart from 'vue3-apexcharts';

export default defineNuxtPlugin(nuxtApp => {
  nuxtApp.vueApp.component('apexchart', apexchart);
});
