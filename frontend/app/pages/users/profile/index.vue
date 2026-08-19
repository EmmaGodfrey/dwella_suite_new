<template>
  <TheBreadcrumbs main="Users" title="Users Profile" />
  <div class="container-fluid">
    <div class="user-profile">
      <div class="row">
        <UserProfileHeader />
        <UserProfileDefaultAccording />
        <div class="col-xl-9 col-lg-12 xl-65">
          <div class="row">
            <UserProfilePost />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'User Profile| Cion - Premium Nuxt Admin Template',
});
</script>
