<template>
  <div>
    <BreadCrumbs title="Revenue Reports" main="Analytics" />
    <div class="container-fluid">
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
              <button class="btn btn-primary w-100" @click="() => refetch()">
                <i class="fa fa-refresh me-1"></i>Apply
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header pb-0"><h5>Revenue Over Time</h5></div>
        <div class="card-body">
          <div v-if="isLoading" class="text-center py-5"><div class="spinner-border" role="status"></div></div>
          <apexchart
            v-else-if="series[0].data.length"
            type="bar"
            height="380"
            :options="chartOptions"
            :series="series"
          />
          <div v-else class="text-center py-5 text-muted">
            <i class="fa fa-bar-chart fa-4x mb-3 d-block opacity-25"></i>
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
  name: 'analytics-revenue',
  path: '/analytics/revenue-reports',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Analytics' }, { title: 'Revenue Reports', active: true }])

const store = usePaymentsStore()
const { useFetchPaymentAnalyticsQuery } = usePayments()

const filters = ref({
  from: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
  to: new Date().toISOString().slice(0, 10),
  group_by: 'month',
})

const { isLoading, refetch } = useFetchPaymentAnalyticsQuery(filters)
const data = computed(() => store.analyticsData)

const series = computed(() => [{ name: 'Revenue (ZMW)', data: data.value.map(p => p.value) }])
const chartOptions = computed(() => ({
  chart: { toolbar: { show: false } },
  colors: ['var(--theme-default)'],
  xaxis: { categories: data.value.map(p => p.label) },
  yaxis: { labels: { formatter: (v: number) => `K${v.toLocaleString()}` } },
}))
</script>
