<template>
  <TheBreadcrumbs main="Ecommerce" title="Product Details" />
  <div class="container-fluid">
    <div>
      <div class="row product-page-main p-0">
        <EcommerceProductpageProductSwiper />
        <EcommerceProductpagePageDetails />
        <EcommerceProductpageFilterBlock />
      </div>
    </div>
    <EcommerceProductpageProdectpageTab />
  </div>
</template>
<script lang="ts" setup>
useHead({
  title: 'Product page | Viho - Premium Nuxt Admin Template',
});
</script>
