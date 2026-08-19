<template>
  <section class="maintenance-sec">
    <div class="page-wrapper">
      <div class="error-wrapper maintenance-bg">
        <div class="container">
          <ul class="maintenance-icons">
            <li><i class="fa fa-cog"></i></li>
            <li><i class="fa fa-cog"></i></li>
            <li><i class="fa fa-cog"></i></li>
          </ul>
          <div class="maintenance-heading">
            <h2 class="headline">MAINTENANCE</h2>
          </div>
          <h4 class="sub-content">Our Site is Currently under maintenance We will be back Shortly<br />Thank You For Patience</h4>
          <div><nuxt-link class="btn btn-primary btn-lg text-light" to="/">BACK TO HOME PAGE</nuxt-link></div>
        </div>
      </div>
    </div>
  </section>
</template>
<script lang="ts" setup>
definePageMeta({
  layout: 'custom',
});
useHead({
  title: 'Maintenance | Cion - Premium Vue Admin Template',
});
</script>
