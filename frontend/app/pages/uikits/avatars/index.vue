<template>
  <TheBreadcrumbs main="UI Kits" title="avatars" />
  <div class="container-fluid">
    <div class="user-profile">
      <div class="row">
        <UikitsAvatarSizingAvatar />
        <UikitsAvatarStatusAvatar />
        <UikitsAvatarInitialsAvatar />
        <UikitsAvatarShapAvatar />
        <UikitsAvatarGroupsAvatar />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Uikits Avatars | Cion - Premium Nuxt Admin Template',
});
</script>
