<template>
  <div>
    <BreadCrumbs title="Verification Plans" main="Verifications" />
    <div class="container-fluid">
      <div class="row">
        <div class="col-sm-12">
          <DataTable
            title="Verification Plans"
            :headers="headers"
            :items="plans"
            :loading="isLoading"
            :searchable="false"
          >
            <template #header-actions>
              <button class="btn btn-primary" @click="openCreate">
                <i class="fa fa-plus me-1"></i>Add Plan
              </button>
            </template>

            <template #cell-price="{ row }">
              {{ fmtPrice(row.original.price, row.original.currency) }}
            </template>

            <template #cell-actions="{ row }">
              <div class="dropstart">
                <button class="btn btn-sm btn-light border-0 p-1" type="button"
                  :id="`dd-${row.original.id}`" data-bs-toggle="dropdown"
                  style="width:30px;height:30px;line-height:1;">
                  <i class="fa fa-ellipsis-v"></i>
                </button>
                <ul class="dropdown-menu dropdown-menu-sm" :aria-labelledby="`dd-${row.original.id}`">
                  <li>
                    <a class="dropdown-item dropdown-item-sm" href="#" @click.prevent="openEdit(row.original)">
                      <i class="fa fa-pencil me-2"></i>Edit
                    </a>
                  </li>
                  <li><hr class="dropdown-divider my-1"></li>
                  <li>
                    <a class="dropdown-item dropdown-item-sm text-danger" href="#" @click.prevent="handleDelete(row.original)">
                      <i class="fa fa-trash me-2"></i>Delete
                    </a>
                  </li>
                </ul>
              </div>
            </template>
          </DataTable>
        </div>
      </div>
    </div>

    <!-- Plan Modal -->
    <div class="modal fade" id="planModal" tabindex="-1" ref="modalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ form.id ? 'Edit' : 'Add' }} Verification Plan</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="handleSave">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Name <span class="text-danger">*</span></label>
                <input type="text" class="form-control" v-model="form.name"
                  :class="activeMutation.getFieldError('name') ? 'is-invalid' : ''" required />
                <div class="invalid-feedback" v-if="activeMutation.getFieldError('name')">{{ activeMutation.getFieldError('name') }}</div>
              </div>
              <div class="mb-3">
                <label class="form-label">Price (minor units — ngwee) <span class="text-danger">*</span></label>
                <input type="number" class="form-control" v-model.number="form.price_minor" min="0"
                  :class="activeMutation.getFieldError('price_minor') ? 'is-invalid' : ''" required />
                <small class="text-muted">e.g. 50000 = K500.00</small>
                <div class="invalid-feedback" v-if="activeMutation.getFieldError('price_minor')">{{ activeMutation.getFieldError('price_minor') }}</div>
              </div>
              <div class="mb-3">
                <label class="form-label">Duration (days)</label>
                <input type="number" class="form-control" v-model.number="form.duration_days" min="1" />
              </div>
              <div class="mb-3">
                <label class="form-label">Description</label>
                <textarea class="form-control" v-model="form.description" rows="3"></textarea>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="activeMutation.isPending.value">
                <span v-if="activeMutation.isPending.value" class="spinner-border spinner-border-sm me-2"></span>
                {{ form.id ? 'Update' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { VerificationPlan } from '~/types/verification'
import BreadCrumbs from '~/components/breadCrumbs.vue'
import DataTable from '~/components/tables/DataTable.vue'
import { Modal } from 'bootstrap'

definePageMeta({
  name: 'verification-plans',
  path: '/verifications/plans',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([
  { title: 'Home', url: '/dashboard' },
  { title: 'Verifications', url: '/verifications/pending' },
  { title: 'Plans', active: true },
])

const store = useVerificationsStore()
const { useFetchVerificationPlansQuery, useCreatePlanMutation, useUpdatePlanMutation, useDeletePlanMutation } = useVerifications()
const { isLoading } = useFetchVerificationPlansQuery()
const plans = computed(() => store.plans)

const headers = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'name', title: 'Name' },
  { key: 'price', title: 'Price', width: 130 },
  { key: 'duration_days', title: 'Duration (days)', width: 140 },
  { key: 'description', title: 'Description' },
  { key: 'actions', title: 'Actions', align: 'center', width: 70 },
]

const modalEl = ref<HTMLElement | null>(null)
let modalInstance: Modal | null = null
onMounted(() => { if (modalEl.value) modalInstance = new Modal(modalEl.value) })
onBeforeUnmount(() => modalInstance?.dispose())

const form = ref<any>({ id: null, name: '', price_minor: 0, duration_days: null, description: '' })

const createMutation = useCreatePlanMutation()
const updateMutation = useUpdatePlanMutation()
const deleteMutation = useDeletePlanMutation()
const activeMutation = computed(() => form.value.id ? updateMutation : createMutation)

const openCreate = () => {
  form.value = { id: null, name: '', price_minor: 0, duration_days: null, description: '' }
  createMutation.reset()
  modalInstance?.show()
}

const openEdit = (plan: VerificationPlan) => {
  form.value = { id: plan.id, name: plan.name, price_minor: plan.price_minor, duration_days: plan.duration_days || null, description: plan.description || '' }
  updateMutation.reset()
  modalInstance?.show()
}

const handleSave = async () => {
  try {
    const { id, ...data } = form.value
    if (id) await updateMutation.mutateAsync({ id, data })
    else await createMutation.mutateAsync(data)
    modalInstance?.hide()
  } catch { /* handled */ }
}

const handleDelete = async (plan: VerificationPlan) => {
  if (confirm(`Delete plan "${plan.name}"?`)) await deleteMutation.mutateAsync(plan.id)
}

const fmtPrice = (price?: number, currency?: string) =>
  new Intl.NumberFormat('en-ZM', { style: 'currency', currency: currency || 'ZMW' }).format(price ?? 0)
</script>

<style scoped>
.dropdown-menu-sm { min-width: 8rem; font-size: 0.875rem; }
.dropdown-item-sm { padding: 0.4rem 1rem; font-size: 0.875rem; }
</style>
