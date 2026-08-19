<template>
  <div class="container-fluid dashboard-default-sec">
    <div class="row">
      <DashboardDefault />
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({
  name: 'dashboard',
  path: '/dashboard',
  layout: 'default',
  requiresAuth: true,
  public: false,
})

useHead({
  title: 'Dashboard Defult | Viho - Premium Nuxt Admin Template',
});
</script>
