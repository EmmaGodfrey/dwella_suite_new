<template>
  <TheBreadcrumbs main="Email" title="Email Reading" />
  <div class="container-fluid">
    <div class="email-wrap">
      <div class="row">
        <CommenEmailSidebar />
        <EmailRead />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Email Read | Cion - Premium Nuxt Admin Template',
});
</script>
