<template>
  <TheBreadcrumbs main="Knowledgebase" title="Knowledgebase" />
  <div class="container-fluid faq-section">
    <div class="row">
      <KnowledgebaseKnowledgebaseSearch />
      <KnowledgebaseKnowledgebaseFaqWidgets />
      <KnowledgebaseKnowledgebaseFeaturesFaq />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Knowledgebase | Cion - Premium Vue Admin Template',
});
</script>
