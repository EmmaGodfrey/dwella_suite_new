export default defineNuxtRouteMiddleware((to, from) => {
  // Only check on client-side since sessionStorage is browser-only
  if (process.client) {
    const authToken = sessionStorage.getItem('authToken')
    
    // If user is not logged in, redirect to login
    if (!authToken) {
      return navigateTo('/login')
    }
  }
})
