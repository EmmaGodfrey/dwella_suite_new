<template>
  <TheBreadcrumbs main="Users" title="Users Edit" />
  <div class="container-fluid">
    <div class="edit-profile">
      <div class="row">
        <UserEditUserProfile />
        <UserEditProfile />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'User Edit| Cion - Premium Nuxt Admin Template',
});
</script>
