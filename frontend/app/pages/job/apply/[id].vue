<template>
  <TheBreadcrumbs main="Job Search" title="Apply" />
  <div class="container-fluid">
    <div class="row">
      <CommenJobSidebar />
      <JobApply />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Job Apply | Cion - Premium Vue Admin Template',
});
</script>
