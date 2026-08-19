<template>
  <div>
    <BreadCrumbs title="Application Statistics" main="Applications" />
    <div class="container-fluid">
      <div v-if="isLoading" class="text-center py-5">
        <div class="spinner-border" role="status"></div>
      </div>
      <div v-else class="row g-4">
        <div class="col-xl-3 col-sm-6" v-for="card in cards" :key="card.label">
          <div class="card h-100">
            <div class="card-body text-center">
              <div :class="`bg-light-${card.bg} rounded p-4 mb-3 d-inline-block`">
                <i :class="`${card.icon} fa-3x text-${card.bg}`"></i>
              </div>
              <h2 class="mb-1" :class="`text-${card.bg}`">{{ statistics[card.key] ?? 0 }}</h2>
              <p class="text-muted mb-0">{{ card.label }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({
  name: 'application-statistics',
  path: '/applications/statistics',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([
  { title: 'Home', url: '/dashboard' },
  { title: 'Applications', url: '/applications/all' },
  { title: 'Statistics', active: true },
])

const appStore = useApplicationsStore()
const { useFetchApplicationStatisticsQuery } = useApplications()
const { isLoading } = useFetchApplicationStatisticsQuery()
const statistics = computed(() => appStore.statistics)

const cards = [
  { key: 'total', label: 'Total Applications', bg: 'primary', icon: 'fa fa-file-text-o' },
  { key: 'new', label: 'New', bg: 'info', icon: 'fa fa-inbox' },
  { key: 'contacted', label: 'Contacted', bg: 'warning', icon: 'fa fa-phone' },
  { key: 'accepted', label: 'Accepted', bg: 'success', icon: 'fa fa-check-circle' },
  { key: 'declined', label: 'Declined', bg: 'danger', icon: 'fa fa-times-circle' },
] as const
</script>
