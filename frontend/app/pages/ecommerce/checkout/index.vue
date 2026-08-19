<template>
  <div class="checkout">
    <TheBreadcrumbs main="Ecommerce" title="Checkout" />
    <div class="container-fluid">
      <div class="card">
        <div class="card-header pb-0">
          <h5>Billing Details</h5>
        </div>
        <div class="card-body">
          <form>
            <div class="row">
              <EcommerceCheckoutForm />
              <EcommerceCheckoutDetails />
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Checkout | Cion - Premium Nuxt Admin Template',
});
</script>
