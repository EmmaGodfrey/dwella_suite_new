<template>
  <TheBreadcrumbs main="Job Search" title="List View" />
  <div class="container-fluid">
    <div class="row">
      <CommenJobSidebar />
      <JobList />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Job List | Cion - Premium Vue Admin Template',
});
</script>
