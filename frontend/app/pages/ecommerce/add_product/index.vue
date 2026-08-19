<template>
  <TheBreadcrumbs main="Ecommerce" title="Add Product" />
  <div class="container-fluid add-product">
    <div class="row">
      <EcommerceAddProductDescription />
      <EcommerceAddProductImages />
    </div>
  </div>
</template>

<script setup lang="ts">
useHead({
  title: 'Add Product | Cion - Premium Nuxt Admin Template',
});
</script>
