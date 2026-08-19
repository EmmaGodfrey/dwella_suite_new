<template>
  <div>
    <BreadCrumbs title="User Activity" main="Analytics" />
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
                    <h3 class="mb-0">{{ ov?.[card.key] ?? 0 }}</h3>
                  </div>
                  <div :class="`bg-light-${card.bg} p-3 rounded`">
                    <i :class="`${card.icon} fa-2x text-${card.bg}`"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header pb-0"><h5>Recent Activity</h5></div>
          <div class="card-body p-0">
            <ul class="list-group list-group-flush">
              <li v-for="item in activities" :key="item.id" class="list-group-item px-4 py-3">
                <div class="d-flex gap-3">
                  <div class="activity-dot mt-2"></div>
                  <div>
                    <p class="mb-1">{{ item.description }}</p>
                    <small class="text-muted">
                      {{ item.user?.full_name || 'System' }} &middot; {{ fmtDate(item.created_at) }}
                    </small>
                  </div>
                </div>
              </li>
              <li v-if="!activities.length" class="list-group-item text-center text-muted py-5">
                No recent activity
              </li>
            </ul>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({
  name: 'analytics-user-activity',
  path: '/analytics/user-activity',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Analytics' }, { title: 'User Activity', active: true }])

const dashStore = useAdminDashboardStore()
const isLoading = ref(true)

onMounted(async () => {
  await Promise.allSettled([dashStore.fetchOverview(), dashStore.fetchActivities()])
  isLoading.value = false
})

const ov = computed(() => dashStore.overview)
const activities = computed(() => dashStore.activities)

const cards = [
  { key: 'total_users', label: 'Total Users', bg: 'primary', icon: 'fa fa-users' },
  { key: 'total_organizations', label: 'Organizations', bg: 'info', icon: 'fa fa-building-o' },
  { key: 'active_subscriptions', label: 'Active Subscriptions', bg: 'success', icon: 'fa fa-credit-card' },
  { key: 'total_applications', label: 'Total Applications', bg: 'warning', icon: 'fa fa-file-text-o' },
] as const

const fmtDate = (d: string) =>
  new Date(d).toLocaleDateString('en-ZM', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
</script>

<style scoped>
.activity-dot { width: 8px; height: 8px; min-width: 8px; border-radius: 50%; background: var(--theme-default); }
</style>
