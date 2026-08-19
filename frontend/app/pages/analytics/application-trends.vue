<template>
  <div>
    <BreadCrumbs title="Application Trends" main="Analytics" />
    <div class="container-fluid">
      <div v-if="isLoading" class="text-center py-5"><div class="spinner-border" role="status"></div></div>
      <template v-else>
        <div class="row g-4 mb-4">
          <div class="col-xl-3 col-sm-6" v-for="card in cards" :key="card.label">
            <div class="card h-100">
              <div class="card-body text-center">
                <div :class="`bg-light-${card.bg} rounded p-3 mb-3 d-inline-block`">
                  <i :class="`${card.icon} fa-2x text-${card.bg}`"></i>
                </div>
                <h3 class="mb-1" :class="`text-${card.bg}`">{{ stats[card.key] ?? 0 }}</h3>
                <p class="text-muted mb-0">{{ card.label }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header pb-0"><h5>Application Status Breakdown</h5></div>
          <div class="card-body">
            <apexchart type="donut" height="320" :options="donutOptions" :series="donutSeries" />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({
  name: 'analytics-application-trends',
  path: '/analytics/application-trends',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Analytics' }, { title: 'Application Trends', active: true }])

const appStore = useApplicationsStore()
const { useFetchApplicationStatisticsQuery } = useApplications()
const { isLoading } = useFetchApplicationStatisticsQuery()
const stats = computed(() => appStore.statistics)

const cards = [
  { key: 'total', label: 'Total', bg: 'primary', icon: 'fa fa-file-text-o' },
  { key: 'new', label: 'New', bg: 'info', icon: 'fa fa-inbox' },
  { key: 'accepted', label: 'Accepted', bg: 'success', icon: 'fa fa-check-circle' },
  { key: 'declined', label: 'Declined', bg: 'danger', icon: 'fa fa-times-circle' },
] as const

const donutSeries = computed(() => [
  stats.value.new,
  stats.value.contacted,
  stats.value.accepted,
  stats.value.declined,
])

const donutOptions = {
  labels: ['New', 'Contacted', 'Accepted', 'Declined'],
  colors: ['#4099ff', '#f8d62b', '#51bb25', '#dc3545'],
  legend: { position: 'bottom' as const },
}
</script>
