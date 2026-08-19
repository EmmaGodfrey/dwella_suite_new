<template>
  <div>
    <BreadCrumbs title="SMS Settings" main="Settings" />
    <div class="container-fluid">
      <div class="card">
        <div class="card-body text-center py-5">
          <div class="bg-light-success p-4 rounded d-inline-block mb-4">
            <i class="fa fa-mobile fa-4x text-success"></i>
          </div>
          <h4>SMS Settings</h4>
          <p class="text-muted mb-0">
            SMS configuration is not yet available via the API.<br>
            This section will allow you to configure SMS gateway settings when the endpoint is ready.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({ name: 'settings-sms', path: '/settings/sms', layout: 'default', middleware: 'auth', requiresAuth: true, public: false })

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Settings' }, { title: 'SMS', active: true }])
</script>
