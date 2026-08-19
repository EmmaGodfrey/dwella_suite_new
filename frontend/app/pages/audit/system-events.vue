<template>
  <div>
    <BreadCrumbs title="System Events" main="Audit Logs" />
    <div class="container-fluid">
      <div class="card">
        <div class="card-body text-center py-5">
          <div class="bg-light-secondary p-4 rounded d-inline-block mb-4">
            <i class="fa fa-server fa-4x text-secondary"></i>
          </div>
          <h4>System Event Logs</h4>
          <p class="text-muted mb-0">
            System event logging is not yet available via the API.<br>
            This section will display all system-level events (deployments, errors, cron runs) when the endpoint is ready.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({ name: 'audit-system-events', path: '/audit/system-events', layout: 'default', middleware: 'auth', requiresAuth: true, public: false })

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Audit Logs' }, { title: 'System Events', active: true }])
</script>
