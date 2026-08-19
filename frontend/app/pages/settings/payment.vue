<template>
  <div>
    <BreadCrumbs title="Payment Configuration" main="Settings" />
    <div class="container-fluid">
      <div class="row">
        <div class="col-xl-8 col-lg-10">
          <div class="card">
            <div class="card-header pb-0">
              <h5>Payment Settings</h5>
            </div>
            <div class="card-body">
              <div v-if="isLoading" class="text-center py-5">
                <div class="spinner-border" role="status"></div>
              </div>
              <form v-else @submit.prevent="handleSave">
                <template v-if="form && Object.keys(form).length">
                  <div v-for="(value, key) in form" :key="String(key)" class="mb-3">
                    <label class="form-label">{{ formatKey(String(key)) }}</label>
                    <input
                      type="text"
                      class="form-control"
                      v-model="form[key]"
                    />
                  </div>
                </template>
                <div v-else class="alert alert-info">
                  No payment settings returned from the API.
                </div>

                <div class="mt-4 d-flex gap-2">
                  <button type="submit" class="btn btn-primary" :disabled="isSaving">
                    <span v-if="isSaving" class="spinner-border spinner-border-sm me-2"></span>
                    <i v-else class="fa fa-save me-2"></i>Save Settings
                  </button>
                </div>
              </form>
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
  name: 'settings-payment',
  path: '/settings/payment',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Settings', active: true }, { title: 'Payment', active: true }])

const settingsStore = useSettingsStore()
const isLoading = ref(true)
const isSaving = ref(false)
const form = ref<Record<string, any>>({})

onMounted(async () => {
  const response = await settingsStore.fetchPaymentSettings()
  if (response.success && response.data) {
    form.value = { ...response.data }
  }
  isLoading.value = false
})

const handleSave = async () => {
  isSaving.value = true
  try {
    const response = await settingsStore.updatePaymentSettings(form.value)
    if (response.success) {
      toast.success(response.message || 'Settings saved')
    } else {
      toast.error(response.message || 'Failed to save settings')
    }
  } catch {
    toast.error('An error occurred')
  } finally {
    isSaving.value = false
  }
}

const formatKey = (key: string) =>
  key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
</script>
