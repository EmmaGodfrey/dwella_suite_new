<template>
  <TheBreadcrumbs main="Knowledgebase" title="Knowledgebase Category" />
  <div class="container-fluid faq-section">
    <div class="row">
      <KnowledgebaseKnowledgebaseSearch />
      <KnowledgebaseKnowledgebaseFaqWidgets />
      <KnowledgebaseCategoryBrowseArticles />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Knowledgebase Category| Cion - Premium Vue Admin Template',
});
</script>
