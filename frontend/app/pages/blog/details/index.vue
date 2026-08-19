<template>
  <TheBreadcrumbs main="Blog" title="Blog Details" />
  <div class="container-fluid blog-page">
    <div class="row">
      <BlogDetailsBlogShadow />
      <BlogDetailsBlogList />
      <BlogDetailsBlogGrid />
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Blog Details| Cion - Premium Nuxt Admin Template',
});
</script>
