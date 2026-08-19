<template>
  <div>
    <BreadCrumbs title="Email Settings" main="Settings" />
    <div class="container-fluid">
      <div class="row">
        <div class="col-xl-6">
          <div class="card">
            <div class="card-header pb-0"><h5>Test Email Configuration</h5></div>
            <div class="card-body">
              <p class="text-muted">
                Send a test email to verify your email configuration is working correctly.
              </p>
              <form @submit.prevent="handleSend">
                <div class="mb-3">
                  <label class="form-label">Recipient Email <span class="text-danger">*</span></label>
                  <input
                    type="email"
                    class="form-control"
                    v-model="email"
                    placeholder="test@example.com"
                    required
                  />
                </div>
                <button type="submit" class="btn btn-primary" :disabled="isSending">
                  <span v-if="isSending" class="spinner-border spinner-border-sm me-2"></span>
                  <i v-else class="fa fa-send me-2"></i>
                  Send Test Email
                </button>
              </form>
            </div>
          </div>

          <div class="card mt-4">
            <div class="card-header pb-0"><h5>Email Configuration</h5></div>
            <div class="card-body">
              <div class="alert alert-info mb-0">
                <i class="fa fa-info-circle me-2"></i>
                Email configuration (SMTP host, port, credentials) is managed through
                environment variables on the server. Contact your system administrator
                to update these settings.
              </div>
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
  name: 'settings-email',
  path: '/settings/email',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Settings' }, { title: 'Email', active: true }])

const settingsStore = useSettingsStore()
const email = ref('')
const isSending = ref(false)

const handleSend = async () => {
  isSending.value = true
  try {
    const response = await settingsStore.sendTestEmail(email.value)
    if (response.success) {
      toast.success(response.message || 'Test email sent!')
    } else {
      toast.error(response.message || 'Failed to send test email')
    }
  } catch {
    toast.error('An error occurred')
  } finally {
    isSending.value = false
  }
}
</script>
