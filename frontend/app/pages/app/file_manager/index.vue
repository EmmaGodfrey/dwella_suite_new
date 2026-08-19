<template>
  <TheBreadcrumbs main="Apps" title="File Manager" />
  <div class="container-fluid">
    <div class="row">
      <FilemanegerFileSidebar />
      <FilemanegerFileContent />
    </div>
  </div>
</template>
<script lang="ts" setup>
useHead({
  title: 'App File Manager | Viho - Premium Nuxt Admin Template',
});
</script>
