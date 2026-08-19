<template>
  <div>
    <BreadCrumbs title="Applications" main="Admin" />

    <div class="container-fluid">
      <!-- Stats Cards -->
      <div class="row mb-4">
        <div class="col" v-for="stat in statCards" :key="stat.label">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">{{ stat.label }}</p>
                  <h4 class="mb-0" :class="stat.color">{{ statistics[stat.key] ?? 0 }}</h4>
                </div>
                <div :class="`bg-light-${stat.bg} p-3 rounded`">
                  <i :class="`${stat.icon} fa-2x text-${stat.bg}`"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Status tabs + DataTable -->
      <div class="row">
        <div class="col-sm-12">
          <div class="card">
            <div class="card-body pb-0">
              <ul class="nav nav-tabs border-tab" role="tablist">
                <li class="nav-item" v-for="tab in tabs" :key="tab.status">
                  <a
                    class="nav-link"
                    :class="{ active: activeStatus === tab.status }"
                    @click.prevent="setStatus(tab.status)"
                    href="#"
                  >{{ tab.label }}</a>
                </li>
              </ul>
            </div>
          </div>

          <DataTable
            :title="activeTabLabel"
            :headers="headers"
            :items="applications"
            :loading="isLoading"
            :items-per-page="params.per_page"
            :total-items="appStore.pagination.total"
            :current-page="params.page"
            :searchable="true"
            @update:current-page="p => { params.page = p }"
            @update:items-per-page="n => { params.per_page = n; params.page = 1 }"
            @update:search="s => { params.search = s; params.page = 1 }"
          >
            <template #cell-status="{ row }">
              <span class="badge" :class="statusBadge(row.original.status)">
                {{ row.original.status }}
              </span>
            </template>

            <template #cell-listing="{ row }">
              <span class="small">{{ row.original.listing?.title || '—' }}</span>
            </template>

            <template #cell-applicant="{ row }">
              <div>
                <div>{{ row.original.applicant?.full_name || '—' }}</div>
                <small class="text-muted">{{ row.original.applicant?.email }}</small>
              </div>
            </template>

            <template #cell-created_at="{ row }">
              {{ fmtDate(row.original.created_at) }}
            </template>

            <template #cell-actions="{ row }">
              <NuxtLink :to="`/applications/${row.original.id}`" class="btn btn-sm btn-outline-primary">
                <i class="fa fa-eye"></i>
              </NuxtLink>
            </template>
          </DataTable>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ApplicationsListParams } from '~/types/application'
import BreadCrumbs from '~/components/breadCrumbs.vue'
import DataTable from '~/components/tables/DataTable.vue'

definePageMeta({
  name: 'applications',
  path: '/applications/all',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Applications', active: true }])

const appStore = useApplicationsStore()
const { useFetchApplicationsQuery, useFetchApplicationStatisticsQuery } = useApplications()

const tabs = [
  { status: '', label: 'All' },
  { status: 'new', label: 'New' },
  { status: 'contacted', label: 'Contacted' },
  { status: 'accepted', label: 'Accepted' },
  { status: 'declined', label: 'Declined' },
]
const activeStatus = ref('')
const activeTabLabel = computed(() => tabs.find(t => t.status === activeStatus.value)?.label ?? 'All')

const params = ref<ApplicationsListParams>({ page: 1, per_page: 15, search: '' })

const setStatus = (status: string) => {
  activeStatus.value = status
  params.value['filter[status]'] = status || undefined
  params.value.page = 1
}

const { isLoading } = useFetchApplicationsQuery(params)
useFetchApplicationStatisticsQuery()

const applications = computed(() => appStore.applications)
const statistics = computed(() => appStore.statistics)

const statCards = [
  { key: 'total', label: 'Total', color: '', bg: 'primary', icon: 'fa fa-file-text-o' },
  { key: 'new', label: 'New', color: 'text-info', bg: 'info', icon: 'fa fa-inbox' },
  { key: 'contacted', label: 'Contacted', color: 'text-warning', bg: 'warning', icon: 'fa fa-phone' },
  { key: 'accepted', label: 'Accepted', color: 'text-success', bg: 'success', icon: 'fa fa-check-circle' },
  { key: 'declined', label: 'Declined', color: 'text-danger', bg: 'danger', icon: 'fa fa-times-circle' },
] as const

const headers = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'applicant', title: 'Applicant' },
  { key: 'listing', title: 'Listing' },
  { key: 'status', title: 'Status', width: 110 },
  { key: 'created_at', title: 'Date', width: 130 },
  { key: 'actions', title: '', align: 'center', width: 60 },
]

const statusBadge = (s: string) => ({
  new: 'badge-info',
  contacted: 'badge-warning',
  accepted: 'badge-success',
  declined: 'badge-danger',
}[s] || 'badge-secondary')

const fmtDate = (d: string) =>
  new Date(d).toLocaleDateString('en-ZM', { year: 'numeric', month: 'short', day: 'numeric' })
</script>

<style scoped>
.nav-tabs .nav-link { cursor: pointer; }
.badge-info      { background-color: #4099ff; }
.badge-warning   { background-color: #f8d62b; color: #000; }
.badge-success   { background-color: #51bb25; }
.badge-danger    { background-color: #dc3545; }
.badge-secondary { background-color: #6c757d; }
</style>
