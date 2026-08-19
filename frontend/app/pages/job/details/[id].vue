<template>
  <TheBreadcrumbs main="Job Search" title="Job Details" />
  <div class="container-fluid">
    <div class="row">
      <CommenJobSidebar />
      <JobDetails />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Job Details | Cion - Premium Vue Admin Template',
});
</script>
