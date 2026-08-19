<template>
  <div>
    <BreadCrumbs title="Listings Report" main="Reports" />
    <div class="container-fluid">
      <DataTable
        title="Listings Report"
        :headers="headers"
        :items="listings"
        :loading="isLoading"
        :items-per-page="params.per_page"
        :total-items="listingsStore.pagination.total"
        :current-page="params.page"
        :searchable="true"
        @update:current-page="p => { params.page = p }"
        @update:items-per-page="n => { params.per_page = n; params.page = 1 }"
        @update:search="s => { params.search = s; params.page = 1 }"
      >
        <template #cell-status="{ row }">
          <span class="badge" :class="statusBadge(row.original.status)">{{ row.original.status }}</span>
        </template>
        <template #cell-price="{ row }">
          {{ fmtPrice(row.original.price, row.original.currency) }}/{{ row.original.price_period }}
        </template>
        <template #cell-organization="{ row }">
          {{ row.original.organization?.name || '—' }}
        </template>
        <template #cell-created_at="{ row }">
          {{ fmtDate(row.original.created_at) }}
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ListingsListParams } from '~/types/listing'
import BreadCrumbs from '~/components/breadCrumbs.vue'
import DataTable from '~/components/tables/DataTable.vue'

definePageMeta({ name: 'reports-listings', path: '/reports/listings', layout: 'default', middleware: 'auth', requiresAuth: true, public: false })

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Reports' }, { title: 'Listings', active: true }])

const listingsStore = useListingsStore()
const { useFetchListingsQuery } = useListings()
const params = ref<ListingsListParams>({ page: 1, per_page: 25 })
const { isLoading } = useFetchListingsQuery(params)
const listings = computed(() => listingsStore.listings)

const headers = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'title', title: 'Title' },
  { key: 'organization', title: 'Organization' },
  { key: 'price', title: 'Price', width: 160 },
  { key: 'status', title: 'Status', width: 100 },
  { key: 'created_at', title: 'Date', width: 120 },
]

const statusBadge = (s: string) => ({
  draft: 'badge-secondary', pending: 'badge-warning', published: 'badge-success',
  approved: 'badge-info', rejected: 'badge-danger', archived: 'badge-dark',
}[s] || 'badge-secondary')

const fmtPrice = (p?: number, c = 'ZMW') =>
  new Intl.NumberFormat('en-ZM', { style: 'currency', currency: c }).format(p ?? 0)
const fmtDate = (d?: string) =>
  d ? new Date(d).toLocaleDateString('en-ZM', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'
</script>

<style scoped>
.badge-success { background-color: #51bb25; }
.badge-warning { background-color: #f8d62b; color: #000; }
.badge-danger { background-color: #dc3545; }
.badge-info { background-color: #4099ff; }
.badge-secondary { background-color: #6c757d; }
.badge-dark { background-color: #343a40; }
</style>
