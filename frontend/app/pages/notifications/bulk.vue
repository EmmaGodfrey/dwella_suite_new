<template>
  <div>
    <BreadCrumbs title="Bulk Push Notification" main="Notifications" />
    <div class="container-fluid">
      <div class="row">
        <div class="col-xl-8 col-lg-10">
          <div class="card">
            <div class="card-header pb-0">
              <h5>Send Notification</h5>
              <span class="text-muted small">Broadcast to all users or target specific users</span>
            </div>
            <div class="card-body">
              <form @submit.prevent="handleSend">
                <div class="mb-3">
                  <label class="form-label">Title <span class="text-danger">*</span></label>
                  <input
                    type="text"
                    class="form-control"
                    v-model="form.title"
                    :class="getFieldError('title') ? 'is-invalid' : ''"
                    required
                    placeholder="Notification title"
                  />
                  <div class="invalid-feedback" v-if="getFieldError('title')">{{ getFieldError('title') }}</div>
                </div>

                <div class="mb-3">
                  <label class="form-label">Message <span class="text-danger">*</span></label>
                  <textarea
                    class="form-control"
                    v-model="form.message"
                    :class="getFieldError('message') ? 'is-invalid' : ''"
                    rows="5"
                    required
                    placeholder="Notification body..."
                  ></textarea>
                  <div class="invalid-feedback" v-if="getFieldError('message')">{{ getFieldError('message') }}</div>
                </div>

                <div class="mb-4">
                  <div class="form-check form-switch">
                    <input
                      class="form-check-input"
                      type="checkbox"
                      id="sendToAll"
                      v-model="form.send_to_all"
                    />
                    <label class="form-check-label" for="sendToAll">
                      <strong>Send to all users</strong>
                    </label>
                  </div>
                </div>

                <div v-if="!form.send_to_all" class="mb-4">
                  <label class="form-label">Target User IDs</label>
                  <textarea
                    class="form-control"
                    v-model="userIdsRaw"
                    rows="3"
                    placeholder="Comma-separated user IDs e.g. 1, 2, 3"
                  ></textarea>
                  <small class="text-muted">Enter comma-separated user IDs</small>
                </div>

                <div class="alert alert-info d-flex align-items-start gap-2" v-if="form.send_to_all">
                  <i class="fa fa-info-circle mt-1"></i>
                  <span>This notification will be sent to <strong>all {{ form.send_to_all ? 'registered' : 'selected' }} users</strong>.</span>
                </div>

                <div class="d-flex gap-2">
                  <button type="submit" class="btn btn-primary" :disabled="sendMutation.isPending.value">
                    <span v-if="sendMutation.isPending.value" class="spinner-border spinner-border-sm me-2"></span>
                    <i v-else class="fa fa-send me-2"></i>
                    Send Notification
                  </button>
                  <NuxtLink to="/notifications/history" class="btn btn-secondary">
                    Cancel
                  </NuxtLink>
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
  name: 'notification-bulk',
  path: '/notifications/bulk',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([
  { title: 'Home', url: '/dashboard' },
  { title: 'Notifications', url: '/notifications/history' },
  { title: 'Bulk Push', active: true },
])

const { useSendBulkPushMutation } = useNotificationsAdmin()
const sendMutation = useSendBulkPushMutation()
const { getFieldError } = sendMutation

const form = ref({ title: '', message: '', send_to_all: true })
const userIdsRaw = ref('')

const handleSend = async () => {
  const userIds = userIdsRaw.value
    .split(',')
    .map(s => parseInt(s.trim(), 10))
    .filter(n => !isNaN(n))

  await sendMutation.mutateAsync({
    title: form.value.title,
    message: form.value.message,
    send_to_all: form.value.send_to_all,
    user_ids: form.value.send_to_all ? [] : userIds,
  })

  if (!sendMutation.isError.value) {
    form.value = { title: '', message: '', send_to_all: true }
    userIdsRaw.value = ''
  }
}
</script>
