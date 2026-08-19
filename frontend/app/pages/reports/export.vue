<template>
  <div>
    <BreadCrumbs title="Export Data" main="Reports" />
    <div class="container-fluid">
      <div class="row g-4">
        <div class="col-xl-4 col-md-6" v-for="item in exports" :key="item.label">
          <div class="card h-100">
            <div class="card-body d-flex flex-column">
              <div :class="`bg-light-${item.bg} p-3 rounded mb-3 d-inline-block`">
                <i :class="`${item.icon} fa-2x text-${item.bg}`"></i>
              </div>
              <h5 class="mb-2">{{ item.label }}</h5>
              <p class="text-muted flex-grow-1">{{ item.description }}</p>
              <button
                class="btn w-100"
                :class="`btn-outline-${item.bg}`"
                @click="handleExport(item)"
                :disabled="item.loading"
              >
                <span v-if="item.loading" class="spinner-border spinner-border-sm me-2"></span>
                <i v-else class="fa fa-download me-2"></i>
                Export CSV
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'
import { toast } from 'vue3-toastify'

definePageMeta({ name: 'reports-export', path: '/reports/export', layout: 'default', middleware: 'auth', requiresAuth: true, public: false })

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Reports' }, { title: 'Export Data', active: true }])

const { $api } = useNuxtApp() as any

const exports = ref([
  { label: 'Users Export', description: 'Download all registered users as CSV.', endpoint: '/admin/users', bg: 'primary', icon: 'fa fa-users', loading: false },
  { label: 'Listings Export', description: 'Download all listings with status and pricing.', endpoint: '/admin/listings', bg: 'success', icon: 'fa fa-home', loading: false },
  { label: 'Payments Export', description: 'Download all payment transactions.', endpoint: '/admin/payments', bg: 'info', icon: 'fa fa-dollar', loading: false },
  { label: 'Applications Export', description: 'Download all tenant applications.', endpoint: '/admin/applications', bg: 'warning', icon: 'fa fa-file-text-o', loading: false },
])

const handleExport = async (item: (typeof exports.value)[0]) => {
  item.loading = true
  try {
    const response = await $api.get(item.endpoint, { params: { export: true } })
    if (response.success) {
      toast.success('Export ready — check your downloads or email.')
    } else {
      toast.error(response.message || 'Export failed')
    }
  } catch {
    toast.error('Export failed')
  } finally {
    item.loading = false
  }
}
</script>
