<template>
  <div class="container-fluid dashboard-default-sec">
    <div class="row">
      <DashboardDefault />
    </div>
  </div>
</template>
<script lang="ts" setup>
definePageMeta({
  name: 'home',
  path: '/',
  layout: 'default',
  requiresAuth: true,
  public: false,
})

useHead({
  title: 'Viho - Premium Nuxt Admin Template',
});

const router = useRouter();
const hasRedirected = ref(false);

onMounted(() => {
  if (!hasRedirected.value && router.currentRoute.value.path === '/') {
    hasRedirected.value = true;
    router.replace('/dashboard');
  }
});
</script>
