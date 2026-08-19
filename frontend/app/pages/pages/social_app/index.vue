<template>
  <TheBreadcrumbs main="Apps" title="Social App" />
  <div class="container-fluid">
    <div class="user-profile social-app-profile">
      <div class="row">
        <ClientOnly>
          <SocialappSocialHeader />
        </ClientOnly>
        <SocialappSoicalTab />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Social App| Cion - Premium Nuxt Admin Template',
});
</script>
