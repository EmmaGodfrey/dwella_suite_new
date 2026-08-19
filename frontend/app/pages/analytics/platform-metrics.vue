<template>
  <div>
    <BreadCrumbs title="Platform Metrics" main="Analytics" />
    <div class="container-fluid">
      <div v-if="isLoading" class="text-center py-5"><div class="spinner-border" role="status"></div></div>
      <template v-else>
        <div class="row g-4 mb-4">
          <div class="col-xl-3 col-sm-6" v-for="card in cards" :key="card.label">
            <div class="card h-100">
              <div class="card-body">
                <div class="d-flex align-items-center justify-content-between">
                  <div>
                    <p class="text-muted mb-1">{{ card.label }}</p>
                    <h3 class="mb-0" :class="card.color">{{ card.value }}</h3>
                  </div>
                  <div :class="`bg-light-${card.bg} p-3 rounded`">
                    <i :class="`${card.icon} fa-2x text-${card.bg}`"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({
  name: 'analytics-platform-metrics',
  path: '/analytics/platform-metrics',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Analytics' }, { title: 'Platform Metrics', active: true }])

const dashStore = useAdminDashboardStore()
const isLoading = ref(true)

onMounted(async () => {
  await dashStore.fetchOverview()
  isLoading.value = false
})

const ov = computed(() => dashStore.overview)

const cards = computed(() => [
  { label: 'Total Users', value: (ov.value?.total_users ?? 0).toLocaleString(), bg: 'primary', color: '', icon: 'fa fa-users' },
  { label: 'Total Listings', value: (ov.value?.total_listings ?? 0).toLocaleString(), bg: 'success', color: 'text-success', icon: 'fa fa-home' },
  { label: 'Organizations', value: (ov.value?.total_organizations ?? 0).toLocaleString(), bg: 'warning', color: 'text-warning', icon: 'fa fa-building-o' },
  { label: 'Total Applications', value: (ov.value?.total_applications ?? 0).toLocaleString(), bg: 'info', color: 'text-info', icon: 'fa fa-file-text-o' },
  { label: 'Active Subscriptions', value: (ov.value?.active_subscriptions ?? 0).toLocaleString(), bg: 'secondary', color: '', icon: 'fa fa-credit-card' },
  { label: 'Pending Verifications', value: (ov.value?.pending_verifications ?? 0).toLocaleString(), bg: 'danger', color: 'text-danger', icon: 'fa fa-shield' },
  { label: 'Pending Listings', value: (ov.value?.pending_listings ?? 0).toLocaleString(), bg: 'warning', color: 'text-warning', icon: 'fa fa-clock-o' },
  { label: 'Total Revenue', value: new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' }).format(ov.value?.total_revenue ?? 0), bg: 'primary', color: 'text-primary', icon: 'fa fa-dollar' },
])
</script>
