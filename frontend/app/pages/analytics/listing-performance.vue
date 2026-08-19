<template>
  <div>
    <BreadCrumbs title="Listing Performance" main="Analytics" />
    <div class="container-fluid">
      <div v-if="isLoading" class="text-center py-5"><div class="spinner-border" role="status"></div></div>
      <template v-else>
        <div class="row g-4 mb-4">
          <div class="col-xl-2 col-sm-4" v-for="card in cards" :key="card.label">
            <div class="card h-100">
              <div class="card-body text-center">
                <h2 class="mb-1" :class="card.color">{{ stats[card.key] ?? 0 }}</h2>
                <p class="text-muted mb-0 small">{{ card.label }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header pb-0"><h5>Listing Status Distribution</h5></div>
          <div class="card-body">
            <apexchart type="donut" height="350" :options="donutOptions" :series="donutSeries" />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({
  name: 'analytics-listing-performance',
  path: '/analytics/listing-performance',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Analytics' }, { title: 'Listing Performance', active: true }])

const listingsStore = useListingsStore()
const { useFetchStatisticsQuery } = useListings()
const { isLoading } = useFetchStatisticsQuery()
const stats = computed(() => listingsStore.statistics)

const cards = [
  { key: 'total', label: 'Total', color: '' },
  { key: 'published', label: 'Published', color: 'text-success' },
  { key: 'pending', label: 'Pending', color: 'text-warning' },
  { key: 'draft', label: 'Draft', color: '' },
  { key: 'rejected', label: 'Rejected', color: 'text-danger' },
  { key: 'archived', label: 'Archived', color: 'text-secondary' },
] as const

const donutSeries = computed(() => [
  stats.value.published,
  stats.value.pending,
  stats.value.draft,
  stats.value.rejected,
  stats.value.archived,
])

const donutOptions = {
  labels: ['Published', 'Pending', 'Draft', 'Rejected', 'Archived'],
  colors: ['#51bb25', '#f8d62b', '#6c757d', '#dc3545', '#343a40'],
  legend: { position: 'bottom' as const },
}
</script>
