export default defineNuxtRouteMiddleware((to, from) => {
  // Only run on client-side to avoid SSR issues
  if (process.server) return

  const publicPaths = ['/login', '/register', '/forgot-password'];
  
  // Check authentication state from sessionStorage directly to avoid timing issues
  const hasToken = process.client ? !!sessionStorage.getItem('authToken') : false;
  const hasUser = process.client ? !!sessionStorage.getItem('authUser') : false;
  const isAuthenticated = hasToken && hasUser;

  // Prevent redirect loops
  if (to.path === from.path) return

  // Allow root path to redirect naturally
  if (to.path === '/') return

  if (isAuthenticated) {
    // If authenticated and trying to access login, redirect to dashboard
    if (publicPaths.includes(to.path)) {
      return navigateTo('/dashboard', { replace: true });
    }
  } else {
    // If not authenticated and trying to access protected route, redirect to login
    if (!publicPaths.includes(to.path)) {
      return navigateTo('/login', { replace: true });
    }
  }
});
