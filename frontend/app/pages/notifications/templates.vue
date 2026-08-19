<template>
  <div>
    <BreadCrumbs title="Notification Templates" main="Notifications" />
    <div class="container-fluid">
      <div v-if="isLoading" class="text-center py-5">
        <div class="spinner-border" role="status"></div>
      </div>
      <div v-else-if="!templates.length" class="card">
        <div class="card-body text-center py-5 text-muted">
          <i class="fa fa-file-text-o fa-4x mb-3 d-block opacity-25"></i>
          <p>No notification templates found</p>
        </div>
      </div>
      <div v-else class="row g-3">
        <div class="col-xl-4 col-md-6" v-for="tpl in templates" :key="tpl.id">
          <div class="card h-100">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start mb-3">
                <h6 class="mb-0">{{ tpl.name }}</h6>
                <span class="badge badge-secondary small">{{ tpl.type || 'generic' }}</span>
              </div>
              <p class="fw-bold mb-1">{{ tpl.title }}</p>
              <p class="text-muted small mb-0" style="white-space: pre-wrap;">{{ tpl.message }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({
  name: 'notification-templates',
  path: '/notifications/templates',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([
  { title: 'Home', url: '/dashboard' },
  { title: 'Notifications', url: '/notifications/history' },
  { title: 'Templates', active: true },
])

const store = useNotificationsAdminStore()
const { useFetchTemplatesQuery } = useNotificationsAdmin()
const { isLoading } = useFetchTemplatesQuery()
const templates = computed(() => store.templates)
</script>

<style scoped>
.badge-secondary { background-color: #6c757d; }
</style>
