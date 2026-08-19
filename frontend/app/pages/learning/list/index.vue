<template>
  <TheBreadcrumbs main="Learning" title="Learning List" />
  <div class="container-fluid">
    <div class="row learning-block">
      <LearningList />
      <CommenLearningFilter />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Learning List | Cion - Premium Vue Admin Template',
});
</script>
