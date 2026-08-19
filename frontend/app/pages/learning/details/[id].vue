<template>
  <TheBreadcrumbs main="Learning" title="Detailed Course" />
  <div class="container-fluid">
    <div class="row learning-block">
      <LearningCourseDetail />
      <CommenLearningFilter />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'course Detailed | Cion - Premium Vue Admin Template',
});
</script>
