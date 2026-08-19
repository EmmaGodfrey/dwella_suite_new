<template>
  <div>
    <BreadCrumbs title="Payments" main="Admin" />

    <div class="container-fluid">
      <!-- Stats -->
      <div class="row mb-4">
        <div class="col-xl-2 col-sm-6" v-for="card in statCards" :key="card.label">
          <div class="card">
            <div class="card-body">
              <p class="text-muted mb-1">{{ card.label }}</p>
              <h4 class="mb-0" :class="card.color">
                {{ card.format === 'currency' ? fmtCurrency(statistics[card.key]) : (statistics[card.key] ?? 0) }}
              </h4>
            </div>
          </div>
        </div>
      </div>

      <!-- Type tabs -->
      <div class="card mb-3">
        <div class="card-body pb-0">
          <ul class="nav nav-tabs border-tab" role="tablist">
            <li class="nav-item" v-for="tab in tabs" :key="tab.type">
              <a class="nav-link" :class="{ active: activeType === tab.type }"
                @click.prevent="setType(tab.type)" href="#">
                {{ tab.label }}
              </a>
            </li>
          </ul>
        </div>
      </div>

      <DataTable
        title="Transactions"
        :headers="headers"
        :items="payments"
        :loading="isLoading"
        :items-per-page="params.per_page"
        :total-items="store.pagination.total"
        :current-page="params.page"
        :searchable="true"
        @update:current-page="p => { params.page = p }"
        @update:items-per-page="n => { params.per_page = n; params.page = 1 }"
        @update:search="s => { params.search = s; params.page = 1 }"
      >
        <template #cell-amount="{ row }">
          {{ fmtCurrency(row.original.amount, row.original.currency) }}
        </template>

        <template #cell-status="{ row }">
          <span class="badge" :class="statusBadge(row.original.status)">{{ row.original.status }}</span>
        </template>

        <template #cell-user="{ row }">
          <div>
            <div>{{ row.original.user?.full_name || '—' }}</div>
            <small class="text-muted">{{ row.original.user?.email }}</small>
          </div>
        </template>

        <template #cell-created_at="{ row }">
          {{ fmtDate(row.original.created_at) }}
        </template>

        <template #cell-actions="{ row }">
          <NuxtLink :to="`/payments/${row.original.id}`" class="btn btn-sm btn-outline-primary">
            <i class="fa fa-eye"></i>
          </NuxtLink>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PaymentsListParams } from '~/types/payment'
import BreadCrumbs from '~/components/breadCrumbs.vue'
import DataTable from '~/components/tables/DataTable.vue'

definePageMeta({
  name: 'payments',
  path: '/payments/all',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Payments', active: true }])

const store = usePaymentsStore()
const { useFetchPaymentsQuery, useFetchPaymentStatisticsQuery } = usePayments()

const tabs = [
  { type: '', label: 'All Transactions' },
  { type: 'subscription', label: 'Subscriptions' },
  { type: 'verification', label: 'Verifications' },
  { type: 'platform_fee', label: 'Platform Fees' },
  { type: 'refund', label: 'Refunds' },
]
const activeType = ref('')

const params = ref<PaymentsListParams>({ page: 1, per_page: 15, search: '' })

const setType = (type: string) => {
  activeType.value = type
  params.value['filter[payment_type]'] = type || undefined
  params.value.page = 1
}

const { isLoading } = useFetchPaymentsQuery(params)
useFetchPaymentStatisticsQuery()

const payments = computed(() => store.payments)
const statistics = computed(() => store.statistics)

const statCards = [
  { key: 'total', label: 'Total', color: '', format: 'number' },
  { key: 'successful', label: 'Successful', color: 'text-success', format: 'number' },
  { key: 'pending', label: 'Pending', color: 'text-warning', format: 'number' },
  { key: 'failed', label: 'Failed', color: 'text-danger', format: 'number' },
  { key: 'refunded', label: 'Refunded', color: 'text-info', format: 'number' },
  { key: 'total_revenue', label: 'Revenue', color: 'text-primary', format: 'currency' },
] as const

const headers = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'reference', title: 'Reference' },
  { key: 'user', title: 'User' },
  { key: 'payment_type', title: 'Type', width: 130 },
  { key: 'amount', title: 'Amount', width: 130 },
  { key: 'status', title: 'Status', width: 110 },
  { key: 'created_at', title: 'Date', width: 130 },
  { key: 'actions', title: '', align: 'center', width: 60 },
]

const statusBadge = (s: string) => ({
  successful: 'badge-success',
  pending: 'badge-warning',
  failed: 'badge-danger',
  refunded: 'badge-info',
}[s] || 'badge-secondary')

const fmtCurrency = (n?: number, currency = 'ZMW') =>
  new Intl.NumberFormat('en-ZM', { style: 'currency', currency }).format(n ?? 0)

const fmtDate = (d: string) =>
  new Date(d).toLocaleDateString('en-ZM', { year: 'numeric', month: 'short', day: 'numeric' })
</script>

<style scoped>
.nav-tabs .nav-link { cursor: pointer; }
.badge-success   { background-color: #51bb25; }
.badge-warning   { background-color: #f8d62b; color: #000; }
.badge-danger    { background-color: #dc3545; }
.badge-info      { background-color: #4099ff; }
.badge-secondary { background-color: #6c757d; }
</style>
