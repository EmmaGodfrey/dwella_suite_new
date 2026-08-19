<template>
  <div>
    <BreadCrumbs title="Payment Detail" main="Payments" />
    <div class="container-fluid">
      <div v-if="isLoading" class="text-center py-5"><div class="spinner-border" role="status"></div></div>
      <div v-else-if="!payment" class="card">
        <div class="card-body text-center py-5 text-danger">
          <i class="fa fa-exclamation-circle fa-4x mb-3 d-block opacity-50"></i>
          <h5>Payment not found</h5>
          <NuxtLink to="/payments/all" class="btn btn-secondary mt-3">Back</NuxtLink>
        </div>
      </div>
      <template v-else>
        <div class="row mb-3">
          <div class="col-sm-12">
            <div class="card">
              <div class="card-body d-flex align-items-center gap-3">
                <NuxtLink to="/payments/all" class="btn btn-outline-secondary btn-sm">
                  <i class="fa fa-arrow-left me-1"></i>Back
                </NuxtLink>
                <div>
                  <h5 class="mb-1">Payment #{{ payment.id }}</h5>
                  <span class="badge" :class="statusBadge(payment.status)">{{ payment.status }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col-xl-6">
            <div class="card mb-4">
              <div class="card-header pb-0"><h5 class="mb-0">Payment Details</h5></div>
              <div class="card-body">
                <ul class="list-group list-group-flush">
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Reference</span><strong>{{ payment.reference }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Amount</span>
                    <strong class="text-primary">{{ fmtCurrency(payment.amount, payment.currency) }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Type</span><strong>{{ payment.payment_type }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Provider</span><strong>{{ payment.provider || '—' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Phone</span><strong>{{ payment.phone || '—' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Date</span><strong>{{ fmtDate(payment.created_at) }}</strong>
                  </li>
                </ul>
              </div>
            </div>
          </div>
          <div class="col-xl-6">
            <div class="card mb-4">
              <div class="card-header pb-0"><h5 class="mb-0">User / Organization</h5></div>
              <div class="card-body">
                <ul class="list-group list-group-flush">
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Name</span><strong>{{ payment.user?.full_name || '—' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Email</span><strong>{{ payment.user?.email || '—' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Organization</span><strong>{{ payment.organization?.name || '—' }}</strong>
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
import type { Payment } from '~/types/payment'
import BreadCrumbs from '~/components/breadCrumbs.vue'

definePageMeta({
  name: 'payment-detail',
  path: '/payments/:id',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const route = useRoute()
const id = computed(() => Number(route.params.id))
const { setBreadcrumbs } = useBreadcrumbs()
const { useFetchPaymentQuery } = usePayments()
const { data, isLoading } = useFetchPaymentQuery(id)

const payment = computed<Payment | null>(() => {
  const d = data.value as any
  return d?.data ?? d ?? null
})

watch(payment, p => {
  if (p) setBreadcrumbs([
    { title: 'Home', url: '/dashboard' },
    { title: 'Payments', url: '/payments/all' },
    { title: `#${p.id}`, active: true },
  ])
}, { immediate: true })

const statusBadge = (s: string) => ({
  successful: 'badge-success',
  pending: 'badge-warning',
  failed: 'badge-danger',
  refunded: 'badge-info',
}[s] || 'badge-secondary')

const fmtCurrency = (n?: number, currency = 'ZMW') =>
  new Intl.NumberFormat('en-ZM', { style: 'currency', currency }).format(n ?? 0)
const fmtDate = (d: string) =>
  new Date(d).toLocaleDateString('en-ZM', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
</script>

<style scoped>
.badge-success   { background-color: #51bb25; }
.badge-warning   { background-color: #f8d62b; color: #000; }
.badge-danger    { background-color: #dc3545; }
.badge-info      { background-color: #4099ff; }
.badge-secondary { background-color: #6c757d; }
</style>
