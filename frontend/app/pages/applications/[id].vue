<template>
  <div>
    <BreadCrumbs title="Application Detail" main="Applications" />

    <div class="container-fluid">
      <div v-if="isLoading" class="text-center py-5">
        <div class="spinner-border" role="status"></div>
      </div>
      <div v-else-if="!application" class="card">
        <div class="card-body text-center py-5 text-danger">
          <i class="fa fa-exclamation-circle fa-4x mb-3 d-block opacity-50"></i>
          <h5>Application not found</h5>
          <NuxtLink to="/applications/all" class="btn btn-secondary mt-3">
            <i class="fa fa-arrow-left me-2"></i>Back
          </NuxtLink>
        </div>
      </div>

      <template v-else>
        <div class="row mb-3">
          <div class="col-sm-12">
            <div class="card">
              <div class="card-body d-flex align-items-center gap-3">
                <NuxtLink to="/applications/all" class="btn btn-outline-secondary btn-sm">
                  <i class="fa fa-arrow-left me-1"></i>Back
                </NuxtLink>
                <div>
                  <h5 class="mb-1">Application #{{ application.id }}</h5>
                  <span class="badge" :class="statusBadge(application.status)">{{ application.status }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col-xl-6">
            <div class="card mb-4">
              <div class="card-header pb-0"><h5 class="mb-0">Applicant</h5></div>
              <div class="card-body">
                <ul class="list-group list-group-flush">
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Name</span>
                    <strong>{{ application.applicant?.full_name || '—' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Email</span>
                    <strong>{{ application.applicant?.email || '—' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Phone</span>
                    <strong>{{ application.applicant?.phone || '—' }}</strong>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div class="col-xl-6">
            <div class="card mb-4">
              <div class="card-header pb-0"><h5 class="mb-0">Listing</h5></div>
              <div class="card-body">
                <ul class="list-group list-group-flush">
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Title</span>
                    <strong>{{ application.listing?.title || '—' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Organization</span>
                    <strong>{{ application.listing?.organization?.name || '—' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Price</span>
                    <strong>
                      {{ fmtPrice(application.listing?.price, application.listing?.currency) }}
                      / {{ application.listing?.price_period }}
                    </strong>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div class="col-sm-12" v-if="application.message">
            <div class="card mb-4">
              <div class="card-header pb-0"><h5 class="mb-0">Message from Applicant</h5></div>
              <div class="card-body">
                <p class="mb-0" style="white-space: pre-wrap;">{{ application.message }}</p>
              </div>
            </div>
          </div>

          <div class="col-sm-12">
            <div class="card mb-4">
              <div class="card-body">
                <ul class="list-group list-group-flush">
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Applied At</span>
                    <strong>{{ fmtDate(application.created_at) }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Last Updated</span>
                    <strong>{{ fmtDate(application.updated_at) }}</strong>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Application } from '~/types/application'
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({
  name: 'application-detail',
  path: '/applications/:id',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const route = useRoute()
const id = computed(() => Number(route.params.id))
const { setBreadcrumbs } = useBreadcrumbs()
const { useFetchApplicationQuery } = useApplications()
const { data, isLoading } = useFetchApplicationQuery(id)

const application = computed<Application | null>(() => {
  const d = data.value as any
  return d?.data ?? d ?? null
})

watch(application, a => {
  if (a) setBreadcrumbs([
    { title: 'Home', url: '/dashboard' },
    { title: 'Applications', url: '/applications/all' },
    { title: `#${a.id}`, active: true },
  ])
}, { immediate: true })

const statusBadge = (s: string) => ({
  new: 'badge-info',
  contacted: 'badge-warning',
  accepted: 'badge-success',
  declined: 'badge-danger',
}[s] || 'badge-secondary')

const fmtDate = (d: string) =>
  new Date(d).toLocaleDateString('en-ZM', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })

const fmtPrice = (price?: number, currency?: string) =>
  new Intl.NumberFormat('en-ZM', { style: 'currency', currency: currency || 'ZMW' }).format(price ?? 0)
</script>

<style scoped>
.badge-info      { background-color: #4099ff; }
.badge-warning   { background-color: #f8d62b; color: #000; }
.badge-success   { background-color: #51bb25; }
.badge-danger    { background-color: #dc3545; }
.badge-secondary { background-color: #6c757d; }
</style>
