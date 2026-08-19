<template>
  <TheBreadcrumbs main="Ecommerce" title="Order Details" />
  <div class="container-fluid">
    <div class="row">
      <div class="col-sm-12">
        <div class="card">
          <div class="card-header pb-0">
            <h5>Order History</h5>
          </div>
          <div class="card-body">
            <EcommerceOrderhistoryOrderdetail />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Order History | Cion - Premium Nuxt Admin Template',
});
</script>
