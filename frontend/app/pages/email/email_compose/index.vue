<template>
  <TheBreadcrumbs main="Email" title="Email Compose" />
  <div class="container-fluid">
    <div class="email-wrap">
      <div class="row">
        <CommenEmailSidebar />
        <email-compose />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Email Compose | Cion - Premium Nuxt Admin Template',
});
</script>
