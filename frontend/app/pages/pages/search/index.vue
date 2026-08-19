<template>
  <TheBreadcrumbs main="Search Pages" title="Search Website" />
  <div class="container-fluid search-page">
    <div class="row">
      <div class="col-sm-12">
        <div class="card">
          <SearchBar />
          <SearchTab />
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Search| Cion - Premium Nuxt Admin Template',
});
</script>
