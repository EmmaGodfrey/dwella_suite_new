<template>
  <TheBreadcrumbs main="Apps" title="To-Do" />
  <div class="container-fluid email-wrap bookmark-wrap todo-wrap">
    <div class="row">
      <TodoSidebar />
      <TodoAddTask />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'To Do| Cion - Premium Nuxt Admin Template',
});
</script>
