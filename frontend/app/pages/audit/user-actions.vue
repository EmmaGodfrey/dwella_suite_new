<template>
  <div>
    <BreadCrumbs title="User Actions" main="Audit Logs" />
    <div class="container-fluid">
      <div class="card">
        <div class="card-body text-center py-5">
          <div class="bg-light-warning p-4 rounded d-inline-block mb-4">
            <i class="fa fa-user-secret fa-4x text-warning"></i>
          </div>
          <h4>User Action Logs</h4>
          <p class="text-muted mb-0">
            User action auditing is not yet available via the API.<br>
            This section will log all significant user actions when the endpoint is ready.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({ name: 'audit-user-actions', path: '/audit/user-actions', layout: 'default', middleware: 'auth', requiresAuth: true, public: false })

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Audit Logs' }, { title: 'User Actions', active: true }])
</script>
