<template>
  <TheBreadcrumbs main="Ecommerce" title="Payment Details" />
  <div class="container-fluid credit-card payment-details">
    <div class="row">
      <EcommercePaymentDetailsCreditCard />
      <EcommercePaymentDetailsDebitCard />
      <EcommercePaymentDetailsCodCard />
      <EcommercePaymentDetailsEmiCard />
      <EcommercePaymentDetailsNetBanking />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Payment Detail | Cion - Premium Nuxt Admin Template',
});
</script>
