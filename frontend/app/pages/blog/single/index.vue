<template>
  <TheBreadcrumbs main="Blog" title="Blog Single" />
  <div class="container-fluid">
    <div class="row">
      <div class="col-sm-12">
        <div class="blog-single">
          <BlogSingleBlogDetails />
          <BlogSingleCommentBox />
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Blog Single| Cion - Premium Nuxt Admin Template',
});
</script>
