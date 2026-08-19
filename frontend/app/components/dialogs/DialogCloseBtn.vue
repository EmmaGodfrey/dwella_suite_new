<template>
  <VBtn icon="mdi-close" size="small" variant="text" @click="$emit('close')" />
</template>

<script setup lang="ts">
defineEmits<{
  close: []
}>()
</script>
