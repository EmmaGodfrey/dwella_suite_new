<template>
  <div>
    <BreadCrumbs title="Financial Reports" main="Reports" />
    <div class="container-fluid">
      <!-- Summary cards -->
      <div class="row g-4 mb-4" v-if="!isLoading">
        <div class="col-xl-3 col-sm-6" v-for="card in cards" :key="card.label">
          <div class="card h-100">
            <div class="card-body">
              <p class="text-muted mb-1">{{ card.label }}</p>
              <h3 class="mb-0" :class="card.color">{{ card.value }}</h3>
            </div>
          </div>
        </div>
      </div>

      <DataTable
        title="Payment Transactions"
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
        <template #cell-user="{ row }">{{ row.original.user?.full_name || '—' }}</template>
        <template #cell-created_at="{ row }">{{ fmtDate(row.original.created_at) }}</template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PaymentsListParams } from '~/types/payment'
import BreadCrumbs from '~/components/breadCrumbs.vue'
import DataTable from '~/components/tables/DataTable.vue'

definePageMeta({ name: 'reports-financial', path: '/reports/financial', layout: 'default', middleware: 'auth', requiresAuth: true, public: false })

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Reports' }, { title: 'Financial', active: true }])

const store = usePaymentsStore()
const { useFetchPaymentsQuery, useFetchPaymentStatisticsQuery } = usePayments()
const params = ref<PaymentsListParams>({ page: 1, per_page: 25 })
const { isLoading } = useFetchPaymentsQuery(params)
useFetchPaymentStatisticsQuery()
const payments = computed(() => store.payments)
const stats = computed(() => store.statistics)

const fmt = (n?: number) => new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' }).format(n ?? 0)
const cards = computed(() => [
  { label: 'Total Revenue', value: fmt(stats.value.total_revenue), color: 'text-primary' },
  { label: 'Successful', value: stats.value.successful, color: 'text-success' },
  { label: 'Pending', value: stats.value.pending, color: 'text-warning' },
  { label: 'Failed / Refunded', value: (stats.value.failed || 0) + (stats.value.refunded || 0), color: 'text-danger' },
])

const headers = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'reference', title: 'Reference' },
  { key: 'user', title: 'User' },
  { key: 'payment_type', title: 'Type', width: 120 },
  { key: 'amount', title: 'Amount', width: 130 },
  { key: 'status', title: 'Status', width: 110 },
  { key: 'created_at', title: 'Date', width: 120 },
]

const statusBadge = (s: string) => ({ successful: 'badge-success', pending: 'badge-warning', failed: 'badge-danger', refunded: 'badge-info' }[s] || 'badge-secondary')
const fmtCurrency = (n?: number, c = 'ZMW') => new Intl.NumberFormat('en-ZM', { style: 'currency', currency: c }).format(n ?? 0)
const fmtDate = (d?: string) => d ? new Date(d).toLocaleDateString('en-ZM', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'
</script>

<style scoped>
.badge-success { background-color: #51bb25; }
.badge-warning { background-color: #f8d62b; color: #000; }
.badge-danger { background-color: #dc3545; }
.badge-info { background-color: #4099ff; }
.badge-secondary { background-color: #6c757d; }
</style>
