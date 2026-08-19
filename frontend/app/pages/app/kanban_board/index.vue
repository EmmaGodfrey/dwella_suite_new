<template>
  <TheBreadcrumbs main="Apps" title="Kanban Board" />
  <div class="container-fluid">
    <div class="row">
      <KanbanDefultDemo />
      <KanbanCustomDome />
      <KanbanApiDome />
    </div>
  </div>
</template>
<script lang="ts" setup>
useHead({
  title: 'Apps Kanban Board | Viho - Premium Nuxt Admin Template',
});
</script>
