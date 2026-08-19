<template>
  <TheBreadcrumbs main="Charts" title="Google Chart" />
  <div class="container-fluid">
    <div class="row">
      <ChartsGooglePieChart1 />
      <ChartsGoogleAreaChart />
      <ChartsGooglePieChart2 />
      <ChartsGooglePieChart3 />
      <ChartsGoogleColumnChart />
      <ChartsGoogleGanttChart />
      <ChartsGoogleLineChart />
      <ChartsGoogleComboChart />
      <ChartsGoogleBarChart />
      <ChartsGoogleWordTree />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Chart Google Chart | Cion - Premium Nuxt Admin Template',
});
</script>
