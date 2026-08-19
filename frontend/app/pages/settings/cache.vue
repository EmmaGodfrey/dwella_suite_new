<template>
  <div>
    <BreadCrumbs title="Cache Management" main="Settings" />
    <div class="container-fluid">
      <div class="row">
        <div class="col-xl-6">
          <div class="card">
            <div class="card-header pb-0"><h5>Application Cache</h5></div>
            <div class="card-body">
              <p class="text-muted">
                Clearing the cache will remove all cached data from the server. Use this
                when you notice stale data or after making configuration changes.
              </p>
              <div class="alert alert-warning d-flex align-items-start gap-2">
                <i class="fa fa-exclamation-triangle mt-1"></i>
                <span>This action may temporarily slow down the application while the cache is rebuilt.</span>
              </div>
              <button
                class="btn btn-danger"
                @click="handleClear"
                :disabled="isClearing"
              >
                <span v-if="isClearing" class="spinner-border spinner-border-sm me-2"></span>
                <i v-else class="fa fa-trash me-2"></i>
                Clear Cache
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

definePageMeta({
  name: 'settings-cache',
  path: '/settings/cache',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Settings' }, { title: 'Cache', active: true }])

const settingsStore = useSettingsStore()
const isClearing = ref(false)

const handleClear = async () => {
  if (!confirm('Clear the application cache?')) return
  isClearing.value = true
  try {
    const response = await settingsStore.clearCache()
    if (response.success) {
      toast.success(response.message || 'Cache cleared successfully')
    } else {
      toast.error(response.message || 'Failed to clear cache')
    }
  } catch {
    toast.error('An error occurred')
  } finally {
    isClearing.value = false
  }
}
</script>
