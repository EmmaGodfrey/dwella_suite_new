<template>
  <TheBreadcrumbs main="Ecommerce" title="Pricing" />
  <div class="container-fluid">
    <div class="row">
      <PricingSimplePricing />
      <PricingBlock />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Pricing | Cion - Premium Nuxt Admin Template',
});
</script>
