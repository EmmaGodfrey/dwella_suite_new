<template>
  <button class="btn btn-primary-light" type="button" @click="logOut" :disabled="isLoggingOut">
    <a class="d-flex"> 
      <Icon name="mdi:logout" class="" size="20" />
      {{ isLoggingOut ? 'Logging out...' : 'Log out' }}
    </a>
  </button>
</template>
<script lang="ts" setup>
const authStore = useAuthStore()
const isLoggingOut = ref(false)

async function logOut() {
  if (isLoggingOut.value) return
  
  isLoggingOut.value = true
  try {
    await authStore.logout()
  } catch (error) {
    console.error('Logout failed:', error)
    isLoggingOut.value = false
  }
}
</script>
