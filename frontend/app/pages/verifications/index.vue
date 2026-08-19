<template>
  <div>
    <BreadCrumbs title="Verifications" main="Admin" />

    <div class="container-fluid">
      <!-- Status Tabs -->
      <div class="row mb-3">
        <div class="col-sm-12">
          <div class="card">
            <div class="card-body pb-0">
              <ul class="nav nav-tabs border-tab" role="tablist">
                <li class="nav-item" v-for="tab in tabs" :key="tab.status">
                  <a
                    class="nav-link"
                    :class="{ active: activeStatus === tab.status }"
                    @click.prevent="setStatus(tab.status)"
                    href="#"
                  >
                    <i :class="tab.icon" class="me-2"></i>{{ tab.label }}
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <DataTable
        :title="activeTabLabel"
        :headers="headers"
        :items="verifications"
        :loading="isLoading"
        :items-per-page="params.per_page"
        :total-items="store.pagination.total"
        :current-page="params.page"
        :searchable="true"
        @update:current-page="p => { params.page = p }"
        @update:items-per-page="n => { params.per_page = n; params.page = 1 }"
        @update:search="s => { params.search = s; params.page = 1 }"
      >
        <template #cell-organization="{ row }">
          <div>
            <div>{{ row.original.organization?.name || '—' }}</div>
            <small class="text-muted">{{ row.original.organization?.type }}</small>
          </div>
        </template>

        <template #cell-plan="{ row }">
          {{ row.original.plan?.name || '—' }}
        </template>

        <template #cell-status="{ row }">
          <span class="badge" :class="statusBadge(row.original.status)">
            {{ row.original.status }}
          </span>
        </template>

        <template #cell-created_at="{ row }">
          {{ fmtDate(row.original.created_at) }}
        </template>

        <template #cell-actions="{ row }">
          <div class="d-flex gap-1 justify-content-center">
            <button
              v-if="row.original.status === 'pending'"
              class="btn btn-sm btn-success"
              @click="handleApprove(row.original)"
              :disabled="approveMutation.isPending.value"
              title="Approve"
            >
              <i class="fa fa-check"></i>
            </button>
            <button
              v-if="row.original.status === 'pending'"
              class="btn btn-sm btn-danger"
              @click="openRejectModal(row.original, 'reject')"
              title="Reject"
            >
              <i class="fa fa-times"></i>
            </button>
            <button
              v-if="row.original.status === 'approved'"
              class="btn btn-sm btn-warning"
              @click="openRejectModal(row.original, 'revoke')"
              title="Revoke"
            >
              <i class="fa fa-ban"></i>
            </button>
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Reject / Revoke Modal -->
    <div class="modal fade" id="actionModal" tabindex="-1" ref="actionModalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ actionType === 'reject' ? 'Reject' : 'Revoke' }} Verification</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="handleAction">
            <div class="modal-body">
              <p>
                Organization: <strong>{{ selectedItem?.organization?.name }}</strong>
              </p>
              <div class="mb-3">
                <label class="form-label">Reason <span class="text-danger">*</span></label>
                <textarea
                  class="form-control"
                  v-model="actionReason"
                  rows="4"
                  :class="activeMutation.getFieldError('reason') ? 'is-invalid' : ''"
                  required
                  placeholder="Explain the reason..."
                ></textarea>
                <div class="invalid-feedback" v-if="activeMutation.getFieldError('reason')">
                  {{ activeMutation.getFieldError('reason') }}
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button
                type="submit"
                :class="actionType === 'reject' ? 'btn btn-danger' : 'btn btn-warning'"
                :disabled="activeMutation.isPending.value"
              >
                <span v-if="activeMutation.isPending.value" class="spinner-border spinner-border-sm me-2"></span>
                {{ actionType === 'reject' ? 'Reject' : 'Revoke' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Verification, VerificationsListParams } from '~/types/verification'
import BreadCrumbs from '~/components/breadCrumbs.vue'
import DataTable from '~/components/tables/DataTable.vue'
import { Modal } from 'bootstrap'

definePageMeta({
  name: 'verifications',
  path: '/verifications/pending',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([{ title: 'Home', url: '/dashboard' }, { title: 'Verifications', active: true }])

const store = useVerificationsStore()
const { useFetchVerificationsQuery, useApproveVerificationMutation, useRejectVerificationMutation, useRevokeVerificationMutation } = useVerifications()

const tabs = [
  { status: 'pending', label: 'Pending', icon: 'fa fa-clock-o' },
  { status: 'approved', label: 'Approved', icon: 'fa fa-check-circle' },
  { status: 'rejected', label: 'Rejected', icon: 'fa fa-times-circle' },
  { status: 'revoked', label: 'Revoked', icon: 'fa fa-ban' },
]
const activeStatus = ref('pending')
const activeTabLabel = computed(() => tabs.find(t => t.status === activeStatus.value)?.label ?? 'Verifications')

const params = ref<VerificationsListParams>({ page: 1, per_page: 15, 'filter[status]': 'pending' })

const setStatus = (status: string) => {
  activeStatus.value = status
  params.value['filter[status]'] = status
  params.value.page = 1
}

const { isLoading } = useFetchVerificationsQuery(params)
const verifications = computed(() => store.verifications)

const headers = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'organization', title: 'Organization' },
  { key: 'plan', title: 'Plan' },
  { key: 'status', title: 'Status', width: 110 },
  { key: 'created_at', title: 'Submitted', width: 130 },
  { key: 'actions', title: 'Actions', align: 'center', width: 120 },
]

// Modals
const actionModalEl = ref<HTMLElement | null>(null)
let actionModalInstance: Modal | null = null
onMounted(() => { if (actionModalEl.value) actionModalInstance = new Modal(actionModalEl.value) })
onBeforeUnmount(() => actionModalInstance?.dispose())

const selectedItem = ref<Verification | null>(null)
const actionType = ref<'reject' | 'revoke'>('reject')
const actionReason = ref('')

const approveMutation = useApproveVerificationMutation()
const rejectMutation = useRejectVerificationMutation()
const revokeMutation = useRevokeVerificationMutation()

const activeMutation = computed(() => actionType.value === 'reject' ? rejectMutation : revokeMutation)

const handleApprove = async (item: Verification) => {
  if (confirm(`Approve verification for "${item.organization?.name}"?`)) {
    await approveMutation.mutateAsync(item.id)
  }
}

const openRejectModal = (item: Verification, type: 'reject' | 'revoke') => {
  selectedItem.value = item
  actionType.value = type
  actionReason.value = ''
  rejectMutation.reset()
  revokeMutation.reset()
  actionModalInstance?.show()
}

const handleAction = async () => {
  if (!selectedItem.value) return
  try {
    if (actionType.value === 'reject') {
      await rejectMutation.mutateAsync({ id: selectedItem.value.id, reason: actionReason.value })
    } else {
      await revokeMutation.mutateAsync({ id: selectedItem.value.id, reason: actionReason.value })
    }
    actionModalInstance?.hide()
  } catch { /* handled */ }
}

const statusBadge = (s: string) => ({
  pending: 'badge-warning',
  approved: 'badge-success',
  rejected: 'badge-danger',
  revoked: 'badge-secondary',
}[s] || 'badge-secondary')

const fmtDate = (d: string) =>
  new Date(d).toLocaleDateString('en-ZM', { year: 'numeric', month: 'short', day: 'numeric' })
</script>

<style scoped>
.nav-tabs .nav-link { cursor: pointer; }
.badge-warning   { background-color: #f8d62b; color: #000; }
.badge-success   { background-color: #51bb25; }
.badge-danger    { background-color: #dc3545; }
.badge-secondary { background-color: #6c757d; }
</style>
