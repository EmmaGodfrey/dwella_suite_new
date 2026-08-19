<template>
  <TheBreadcrumbs main="Project" title="project list" />
  <div class="container-fluid">
    <div class="row project-cards">
      <ProjectListProjectTab />
    </div>
  </div>
</template>
<script lang="ts" setup>
useHead({
  title: 'Project List | Viho - Premium Nuxt Admin Template',
});
</script>
