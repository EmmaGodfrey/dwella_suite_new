<template>
  <TheBreadcrumbs main="Email" title="Email Application" />
  <div class="container-fluid">
    <div class="email-wrap">
      <div class="row">
        <CommenEmailSidebar />
        <EmailInboxEmailProfile />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Email Inbox | Cion - Premium Nuxt Admin Template',
});
</script>
