<template>
  <div>
    <BreadCrumbs title="Dashboard" main="Admin" />

    <div class="container-fluid">
      <!-- KPI Cards -->
      <div class="row mb-4">
        <div class="col-xl-3 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Total Users</p>
                  <h3 class="mb-0">{{ fmt(overview?.total_users) }}</h3>
                </div>
                <div class="bg-light-primary p-3 rounded">
                  <i class="fa fa-users fa-2x text-primary"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-xl-3 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Total Listings</p>
                  <h3 class="mb-0">{{ fmt(overview?.total_listings) }}</h3>
                </div>
                <div class="bg-light-success p-3 rounded">
                  <i class="fa fa-home fa-2x text-success"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-xl-3 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Active Subscriptions</p>
                  <h3 class="mb-0">{{ fmt(overview?.active_subscriptions) }}</h3>
                </div>
                <div class="bg-light-warning p-3 rounded">
                  <i class="fa fa-credit-card fa-2x text-warning"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-xl-3 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Total Revenue</p>
                  <h3 class="mb-0">{{ fmtCurrency(overview?.total_revenue) }}</h3>
                </div>
                <div class="bg-light-info p-3 rounded">
                  <i class="fa fa-dollar fa-2x text-info"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Secondary KPIs -->
      <div class="row mb-4">
        <div class="col-xl-3 col-sm-6">
          <div class="card border-warning">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Pending Listings</p>
                  <h4 class="mb-0 text-warning">{{ fmt(overview?.pending_listings) }}</h4>
                </div>
                <div class="bg-light-warning p-3 rounded">
                  <i class="fa fa-clock-o fa-2x text-warning"></i>
                </div>
              </div>
              <NuxtLink to="/listings" class="small text-warning mt-2 d-block">
                Review now <i class="fa fa-arrow-right ms-1"></i>
              </NuxtLink>
            </div>
          </div>
        </div>
        <div class="col-xl-3 col-sm-6">
          <div class="card border-info">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Pending Verifications</p>
                  <h4 class="mb-0 text-info">{{ fmt(overview?.pending_verifications) }}</h4>
                </div>
                <div class="bg-light-info p-3 rounded">
                  <i class="fa fa-shield fa-2x text-info"></i>
                </div>
              </div>
              <NuxtLink to="/verifications/pending" class="small text-info mt-2 d-block">
                Review now <i class="fa fa-arrow-right ms-1"></i>
              </NuxtLink>
            </div>
          </div>
        </div>
        <div class="col-xl-3 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Organizations</p>
                  <h4 class="mb-0">{{ fmt(overview?.total_organizations) }}</h4>
                </div>
                <div class="bg-light-secondary p-3 rounded">
                  <i class="fa fa-building-o fa-2x text-secondary"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-xl-3 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Applications</p>
                  <h4 class="mb-0">{{ fmt(overview?.total_applications) }}</h4>
                </div>
                <div class="bg-light-primary p-3 rounded">
                  <i class="fa fa-file-text-o fa-2x text-primary"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <!-- Revenue Trend Chart -->
        <div class="col-xl-8">
          <div class="card">
            <div class="card-header pb-0">
              <h5 class="mb-0"><i class="fa fa-line-chart me-2"></i>Revenue Trend</h5>
            </div>
            <div class="card-body">
              <div v-if="isLoading" class="text-center py-5">
                <div class="spinner-border" role="status"></div>
              </div>
              <apexchart
                v-else-if="revenueChartOptions.series[0].data.length"
                type="area"
                height="300"
                :options="revenueChartOptions"
                :series="revenueChartOptions.series"
              />
              <div v-else class="text-center py-5 text-muted">
                <i class="fa fa-chart-line fa-3x mb-3 d-block opacity-25"></i>
                <p>No revenue data available</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="col-xl-4">
          <div class="card">
            <div class="card-header pb-0">
              <h5 class="mb-0"><i class="fa fa-history me-2"></i>Recent Activity</h5>
            </div>
            <div class="card-body p-0">
              <div v-if="isLoading" class="text-center py-5">
                <div class="spinner-border" role="status"></div>
              </div>
              <div v-else-if="!activities.length" class="text-center py-5 text-muted">
                <i class="fa fa-inbox fa-3x mb-3 d-block opacity-25"></i>
                <p>No recent activity</p>
              </div>
              <ul v-else class="list-group list-group-flush">
                <li
                  v-for="item in activities.slice(0, 8)"
                  :key="item.id"
                  class="list-group-item px-4 py-3"
                >
                  <div class="d-flex gap-3 align-items-start">
                    <div class="activity-dot mt-1"></div>
                    <div>
                      <p class="mb-1 small">{{ item.description }}</p>
                      <small class="text-muted">
                        {{ item.user?.full_name || 'System' }}
                        &middot; {{ fmtDate(item.created_at) }}
                      </small>
                    </div>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Listings Trend Chart -->
      <div class="row mt-4">
        <div class="col-sm-12">
          <div class="card">
            <div class="card-header pb-0">
              <h5 class="mb-0"><i class="fa fa-bar-chart me-2"></i>Listings Trend</h5>
            </div>
            <div class="card-body">
              <div v-if="isLoading" class="text-center py-5">
                <div class="spinner-border" role="status"></div>
              </div>
              <apexchart
                v-else-if="listingsChartOptions.series[0].data.length"
                type="bar"
                height="280"
                :options="listingsChartOptions"
                :series="listingsChartOptions.series"
              />
              <div v-else class="text-center py-5 text-muted">
                <i class="fa fa-bar-chart fa-3x mb-3 d-block opacity-25"></i>
                <p>No listings trend data available</p>
              </div>
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
  name: 'dashboard',
  path: '/dashboard',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
const dashStore = useAdminDashboardStore()

setBreadcrumbs([{ title: 'Dashboard', active: true }])

const { overview, activities, revenueTrends, listingsTrends, isLoading } = storeToRefs(dashStore)

onMounted(() => {
  dashStore.fetchAll()
})

// Chart configs
const revenueChartOptions = computed(() => ({
  chart: { toolbar: { show: false }, sparkline: { enabled: false } },
  colors: ['var(--theme-default)'],
  stroke: { curve: 'smooth', width: 2 },
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.1 } },
  xaxis: { categories: revenueTrends.value.map(p => p.label) },
  yaxis: { labels: { formatter: (v: number) => fmtCurrency(v) } },
  tooltip: { y: { formatter: (v: number) => fmtCurrency(v) } },
  series: [{ name: 'Revenue', data: revenueTrends.value.map(p => p.value) }],
}))

const listingsChartOptions = computed(() => ({
  chart: { toolbar: { show: false } },
  colors: ['#51bb25'],
  xaxis: { categories: listingsTrends.value.map(p => p.label) },
  series: [{ name: 'Listings', data: listingsTrends.value.map(p => p.value) }],
}))

// Helpers
const fmt = (n?: number) => (n ?? 0).toLocaleString()
const fmtCurrency = (n?: number) =>
  new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' }).format(n ?? 0)
const fmtDate = (d: string) =>
  new Date(d).toLocaleDateString('en-ZM', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
</script>

<style scoped>
.activity-dot {
  width: 8px;
  height: 8px;
  min-width: 8px;
  border-radius: 50%;
  background: var(--theme-default);
}
</style>
