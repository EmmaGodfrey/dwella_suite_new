<template>
  <TheBreadcrumbs main="Knowledgebase" title="Knowledgebase Details" />
  <div class="container-fluid">
    <div class="row">
      <KnowledgebaseDetailsKnowledgeFilter />
      <KnowledgebaseDetailsBlogBox />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Knowledgebase Details| Cion - Premium Vue Admin Template',
});
</script>
