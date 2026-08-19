<template>
  <TheBreadcrumbs main="Widgets" title="chart" />
  <div class="container-fluid chart-widget">
    <div class="row">
      <DashboardWidgetsChartSaleChart />
      <DashboardWidgetsChartProjectsChart />
      <DashboardWidgetsChartProductChart />
      <DashboardWidgetsChartMarketingExpenses />
      <DashboardWidgetsChartTotalEarning />
      <DashboardWidgetsChartLiveProducts />
      <DashboardWidgetsChartTurnoverChart />
      <DashboardWidgetsChartMonthlySales />
      <DashboardWidgetsChartUsesChart />
      <DashboardWidgetsChartBrowserUses />
    </div>
  </div>
</template>
<script lang="ts" setup>
useHead({
  title: 'widgets Chart | Viho - Premium Nuxt Admin Template',
});
</script>
