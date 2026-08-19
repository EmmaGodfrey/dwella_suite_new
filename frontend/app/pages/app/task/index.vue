<template>
  <TheBreadcrumbs main="Apps" title="Tasks" />
  <div class="container-fluid">
    <div class="email-wrap bookmark-wrap">
      <div class="row">
        <TaskSidebar />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Task| Cion - Premium Nuxt Admin Template',
});
</script>
