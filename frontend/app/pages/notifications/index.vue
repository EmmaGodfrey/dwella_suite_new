<template>
  <div>
    <BreadCrumbs title="Notification History" main="Admin" />
    <div class="container-fluid">
      <DataTable
        title="Sent Notifications"
        :headers="headers"
        :items="notifications"
        :loading="isLoading"
        :items-per-page="params.per_page"
        :total-items="store.pagination.total"
        :current-page="params.page"
        :searchable="true"
        @update:current-page="p => { params.page = p }"
        @update:items-per-page="n => { params.per_page = n; params.page = 1 }"
        @update:search="s => { params.search = s; params.page = 1 }"
      >
        <template #header-actions>
          <NuxtLink to="/notifications/bulk" class="btn btn-primary">
            <i class="fa fa-send me-1"></i>Send Notification
          </NuxtLink>
        </template>

        <template #cell-user="{ row }">
          {{ row.original.user?.full_name || 'All Users' }}
        </template>

        <template #cell-created_at="{ row }">
          {{ fmtDate(row.original.created_at) }}
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'
import DataTable from '~/components/tables/DataTable.vue'

definePageMeta({
  name: 'notification-history',
  path: '/notifications/history',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Notifications', active: true }])

const store = useNotificationsAdminStore()
const { useFetchNotificationsQuery } = useNotificationsAdmin()

const params = ref({ page: 1, per_page: 15, search: '' })
const { isLoading } = useFetchNotificationsQuery(params)
const notifications = computed(() => store.notifications)

const headers = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'title', title: 'Title' },
  { key: 'message', title: 'Message' },
  { key: 'user', title: 'Sent To' },
  { key: 'created_at', title: 'Date', width: 130 },
]

const fmtDate = (d: string) =>
  new Date(d).toLocaleDateString('en-ZM', { year: 'numeric', month: 'short', day: 'numeric' })
</script>
