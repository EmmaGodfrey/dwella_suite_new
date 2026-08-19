export default defineNuxtRouteMiddleware((to, from) => {
  // Only check on client-side since sessionStorage is browser-only
  if (process.client) {
    const authToken = sessionStorage.getItem('authToken')
    
    // If user is already logged in, redirect to dashboard
    if (authToken) {
      return navigateTo('/dashboard')
    }
  }
})
