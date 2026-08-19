<template>
  <div>
    <BreadCrumbs title="User Reports" main="Reports" />
    <div class="container-fluid">
      <DataTable
        title="Users Report"
        :headers="headers"
        :items="users"
        :loading="isLoading"
        :items-per-page="params.per_page"
        :total-items="usersStore.pagination.total"
        :current-page="params.page"
        :searchable="true"
        @update:current-page="p => { params.page = p }"
        @update:items-per-page="n => { params.per_page = n; params.page = 1 }"
        @update:search="s => { params.search = s; params.page = 1 }"
      >
        <template #cell-is_admin="{ row }">
          <span class="badge" :class="row.original.is_admin ? 'badge-danger' : 'badge-secondary'">
            {{ row.original.is_admin ? 'Admin' : 'User' }}
          </span>
        </template>
        <template #cell-is_lister="{ row }">
          <span class="badge" :class="row.original.is_lister ? 'badge-success' : 'badge-secondary'">
            {{ row.original.is_lister ? 'Yes' : 'No' }}
          </span>
        </template>
        <template #cell-created_at="{ row }">
          {{ fmtDate(row.original.created_at) }}
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { UsersListParams } from '~/types/user'
import BreadCrumbs from '~/components/breadCrumbs.vue'
import DataTable from '~/components/tables/DataTable.vue'

definePageMeta({ name: 'reports-users', path: '/reports/users', layout: 'default', middleware: 'auth', requiresAuth: true, public: false })

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Reports' }, { title: 'Users', active: true }])

const usersStore = useUsersStore()
const { useFetchUsersQuery } = useUsers()
const params = ref<UsersListParams>({ page: 1, per_page: 25 })
const { isLoading } = useFetchUsersQuery(params)
const users = computed(() => usersStore.users)

const headers = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'full_name', title: 'Name' },
  { key: 'email', title: 'Email' },
  { key: 'phone', title: 'Phone' },
  { key: 'is_admin', title: 'Admin', width: 90 },
  { key: 'is_lister', title: 'Lister', width: 90 },
  { key: 'created_at', title: 'Joined', width: 130 },
]

const fmtDate = (d?: string) =>
  d ? new Date(d).toLocaleDateString('en-ZM', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'
</script>

<style scoped>
.badge-success { background-color: #51bb25; }
.badge-danger { background-color: #dc3545; }
.badge-secondary { background-color: #6c757d; }
</style>
