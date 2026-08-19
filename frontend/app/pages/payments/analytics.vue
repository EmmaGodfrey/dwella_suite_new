<template>
  <div>
    <BreadCrumbs title="Revenue Analytics" main="Payments" />
    <div class="container-fluid">
      <!-- Date range filter -->
      <div class="card mb-4">
        <div class="card-body">
          <div class="row g-3 align-items-end">
            <div class="col-md-3">
              <label class="form-label">From</label>
              <input type="date" class="form-control" v-model="filters.from" />
            </div>
            <div class="col-md-3">
              <label class="form-label">To</label>
              <input type="date" class="form-control" v-model="filters.to" />
            </div>
            <div class="col-md-3">
              <label class="form-label">Group By</label>
              <select class="form-select" v-model="filters.group_by">
                <option value="day">Day</option>
                <option value="week">Week</option>
                <option value="month">Month</option>
                <option value="year">Year</option>
              </select>
            </div>
            <div class="col-md-3">
              <button class="btn btn-primary w-100" @click="refresh">
                <i class="fa fa-refresh me-1"></i>Apply
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Chart -->
      <div class="card">
        <div class="card-header pb-0">
          <h5 class="mb-0"><i class="fa fa-line-chart me-2"></i>Revenue Over Time</h5>
        </div>
        <div class="card-body">
          <div v-if="isLoading" class="text-center py-5">
            <div class="spinner-border" role="status"></div>
          </div>
          <apexchart
            v-else-if="chartSeries[0].data.length"
            type="area"
            height="380"
            :options="chartOptions"
            :series="chartSeries"
          />
          <div v-else class="text-center py-5 text-muted">
            <i class="fa fa-chart-area fa-4x mb-3 d-block opacity-25"></i>
            <p>No data for selected period</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({
  name: 'payment-analytics',
  path: '/payments/analytics',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([
  { title: 'Home', url: '/dashboard' },
  { title: 'Payments', url: '/payments/all' },
  { title: 'Analytics', active: true },
])

const store = usePaymentsStore()
const { useFetchPaymentAnalyticsQuery } = usePayments()

const filters = ref({
  from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
  to: new Date().toISOString().slice(0, 10),
  group_by: 'day',
})

const { isLoading, refetch } = useFetchPaymentAnalyticsQuery(filters)
const refresh = () => refetch()

const analyticsData = computed(() => store.analyticsData)

const chartSeries = computed(() => [{
  name: 'Revenue',
  data: analyticsData.value.map(p => p.value),
}])

const chartOptions = computed(() => ({
  chart: { toolbar: { show: false } },
  colors: ['var(--theme-default)'],
  stroke: { curve: 'smooth', width: 2 },
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.1 } },
  xaxis: { categories: analyticsData.value.map(p => p.label) },
  yaxis: {
    labels: {
      formatter: (v: number) =>
        new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' }).format(v),
    },
  },
  tooltip: {
    y: {
      formatter: (v: number) =>
        new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' }).format(v),
    },
  },
}))
</script>
