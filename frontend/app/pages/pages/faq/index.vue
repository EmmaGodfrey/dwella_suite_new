<template>
  <TheBreadcrumbs main="FAQ" title="FAQ" />
  <div class="container-fluid">
    <div class="faq-wrap">
      <div class="row">
        <FaqWidgets />
        <FaqAccordion />
        <FaqFeaturedTutorial />
        <FaqArticles />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Faq| Cion - Premium Vue Admin Template',
});
</script>
