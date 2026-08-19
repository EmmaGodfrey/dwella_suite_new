<template>
  <div>
    <BreadCrumbs title="Admin Actions" main="Audit Logs" />
    <div class="container-fluid">
      <div class="card">
        <div class="card-body text-center py-5">
          <div class="bg-light-info p-4 rounded d-inline-block mb-4">
            <i class="fa fa-history fa-4x text-info"></i>
          </div>
          <h4>Admin Action Logs</h4>
          <p class="text-muted mb-0">
            Audit logging for admin actions is not yet available via the API.<br>
            This section will display all actions performed by administrators when the endpoint is ready.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({ name: 'audit-admin-actions', path: '/audit/admin-actions', layout: 'default', middleware: 'auth', requiresAuth: true, public: false })

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Audit Logs' }, { title: 'Admin Actions', active: true }])
</script>
