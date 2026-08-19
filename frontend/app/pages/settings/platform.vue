<template>
  <div>
    <BreadCrumbs title="Platform Settings" main="Settings" />
    <div class="container-fluid">
      <div class="card">
        <div class="card-body text-center py-5">
          <div class="bg-light-primary p-4 rounded d-inline-block mb-4">
            <i class="fa fa-cog fa-4x text-primary"></i>
          </div>
          <h4>Platform Settings</h4>
          <p class="text-muted mb-0">
            Platform-wide configuration is not yet available via the API.<br>
            This section will allow you to configure general platform settings when the endpoint is ready.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({ name: 'settings-platform', path: '/settings/platform', layout: 'default', middleware: 'auth', requiresAuth: true, public: false })

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Settings' }, { title: 'Platform', active: true }])
</script>
