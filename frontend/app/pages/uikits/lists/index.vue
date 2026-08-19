<template>
  <TheBreadcrumbs main="UI Kits" title="lists" />
  <div class="container-fluid">
    <div class="row">
      <UikitsListsDefultList />
      <UikitsListsBadgesList />
      <UikitsListsCustomContent />
      <UikitsListsJavaScriptList />
      <UikitsListsWithIcon />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Uikits Lists | Cion - Premium Nuxt Admin Template',
});
</script>
