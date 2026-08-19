<template>
  <TheBreadcrumbs main="Dashboard" title="E-Commerce" />
  <div class="container-fluid dashboard-2-main">
    <div class="row">
      <DashboardEcommerceInvoiceOverview />
      <DashboardEcommerceTopDealer />
      <DashboardEcommerceEcormmerceIncome />
      <DashboardEcommerceActivityTimeline />
      <DashboardEcommerceYearlyGrowth />
    </div>
  </div>
</template>
<script lang="ts" setup>
useHead({
  title: 'Dashboard Ecommerce | Viho - Premium Nuxt Admin Template',
});
</script>
