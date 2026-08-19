<template>
  <div></div>
</template>

<script setup lang="ts">
definePageMeta({
  name: 'notification-send',
  path: '/notifications/send',
  layout: 'default',
  middleware: 'auth',
  public: false,
})

// Alias — redirect to bulk push
navigateTo('/notifications/bulk', { replace: true })
</script>
