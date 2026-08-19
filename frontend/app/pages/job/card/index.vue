<template>
  <TheBreadcrumbs main="Job Search" title="Cards View" />
  <div class="container-fluid">
    <div class="row">
      <CommenJobSidebar />
      <JobCardView />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Job Card | Cion - Premium Vue Admin Template',
});
</script>
